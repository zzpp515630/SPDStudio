#include <Arduino.h>
#include <esp_system.h>
#include "driver/i2c.h"
#include <algorithm>
// I2C配置
static const i2c_port_t I2C_PORT = I2C_NUM_0;
static const gpio_num_t PIN_SDA = GPIO_NUM_8;
static const gpio_num_t PIN_SCL = GPIO_NUM_9;
static const uint32_t I2C_FREQ = 100000;  // 先100k稳定，之后可改400k
// N34C04地址配置
// 基础地址为 0x50 A2=A1=A0=gnd
#define N34C04_BASE_ADDR 0x50  // 基础地址 (A2=A1=A0=0)
// 根据数据手册，Page0和Page1是通过内部寄存器切换的，不是通过改变I2C地址
// 实际上N34C04只有一个I2C地址，通过SPA0/SPA1命令切换内部存储区
#define PAGE_SIZE 256  // 256字节 (2Kb = 256字节)

// Page commands (8-bit on wire)
// SPA0 01101100 0x6c
// SPA1 01101110 0x6e
// RPA  01101101 0x6d
static const uint8_t SPA0_8B = 0x6C;
static const uint8_t SPA1_8B = 0x6E;
static const uint8_t RPA_8B = 0x6D;

// Memory array address: 7-bit 0x50 (A2/A1/A0=0)
static const uint8_t MEM7 = 0x50;
static const uint8_t MEM_W_8B = (MEM7 << 1) | 0;  // 0xA0
static const uint8_t MEM_R_8B = (MEM7 << 1) | 1;  // 0xA1

uint8_t currentAddr = N34C04_BASE_ADDR;

i2c_config_t conf = {};
// 添加数据缓冲区
#define MAX_DATA_SIZE 256
uint8_t rxBuffer[MAX_DATA_SIZE];
uint16_t rxBufferIndex = 0;
bool receivingData = false;

// 发送只有地址的命令（用于 SPA0/SPA1）
static esp_err_t sendAddrOnly(uint8_t addr8) {
  // Step 1: 创建命令链（一个事务的容器）
  i2c_cmd_handle_t cmd = i2c_cmd_link_create();
  // Step 2: START 条件
  i2c_master_start(cmd);
  // Step 3: 写入 1 个字节（这里是地址字节）
  // 第三个参数 true 表示：硬件要检查从机是否 ACK。
  // 如果从机 NACK，这个事务通常会在 cmd_begin 时返回 ESP_FAIL。
  i2c_master_write_byte(cmd, addr8, true);
  // Step 4: STOP 条件
  i2c_master_stop(cmd);
  // Step 5: 执行命令链
  esp_err_t err = i2c_master_cmd_begin(I2C_PORT, cmd, pdMS_TO_TICKS(100));
  // Step 6: 释放命令链
  i2c_cmd_link_delete(cmd);
  return err;
}

static bool setPage(bool page1) {
  esp_err_t err = sendAddrOnly(page1 ? SPA1_8B : SPA0_8B);
  if (err != ESP_OK) {
    Serial.printf("SPA%s error: %s (%d)\n", page1 ? "1" : "0", esp_err_to_name(err), (int)err);
    return false;
  }
  return true;
}

// RPA：ACK=page0, NACK=page1
static int queryPageRPA() {
  esp_err_t err = sendAddrOnly(RPA_8B);
  if (err == ESP_OK) return 0;
  if (err == ESP_FAIL) return 1;  // NACK is meaningful here
  Serial.printf("RPA bus error: %s (%d)\n", esp_err_to_name(err), (int)err);
  return -1;
}

static void hexDump(const uint8_t* buf, size_t len, uint16_t base = 0) {
  Serial.println("DATA_START");
  for (size_t i = 0; i < len; i += 16) {
    Serial.printf("%04X: ", base + (uint16_t)i);
    for (size_t j = 0; j < 16 && (i + j) < len; j++) {
      Serial.printf("%02X ", buf[i + j]);
    }
    Serial.println();
  }
  Serial.println("DATA_END");
}

// Random read from selected page: set word address then read len bytes
static bool memRead(uint8_t wordAddr, uint8_t* out, size_t len) {
  i2c_cmd_handle_t cmd = i2c_cmd_link_create();

  // dummy write: set internal address pointer
  //---- (1) dummy write：设置 word address
  i2c_master_start(cmd);
  // 发内存地址（写）
  i2c_master_write_byte(cmd, MEM_W_8B, true);
  // 发 word address
  i2c_master_write_byte(cmd, wordAddr, true);

  // repeated start then read
  //---- (2) repeated start：切读方向读数据
  i2c_master_start(cmd);
  // 发内存地址（读）
  i2c_master_write_byte(cmd, MEM_R_8B, true);
  // 读 len 字节：前 len-1 个字节回 ACK，最后 1 个字节回 NACK 结束
  if (len > 1) i2c_master_read(cmd, out, len - 1, I2C_MASTER_ACK);
  i2c_master_read_byte(cmd, out + (len - 1), I2C_MASTER_NACK);

  i2c_master_stop(cmd);

  esp_err_t err = i2c_master_cmd_begin(I2C_PORT, cmd, pdMS_TO_TICKS(300));
  i2c_cmd_link_delete(cmd);

  if (err != ESP_OK) {
    Serial.printf("memRead addr=0x%02X len=%u err=%s (%d)\n", wordAddr, (unsigned)len, esp_err_to_name(err), (int)err);
    return false;
  }
  return true;
}

// 读一页256B（分块更稳）
static bool readPage256(bool page1, uint8_t out[256], uint8_t chunk = 32) {
  if (!setPage(page1)) return false;

  int p = queryPageRPA();
  Serial.printf("After SPA%s, RPA=%d\n", page1 ? "1" : "0", p);

  for (uint16_t off = 0; off < 256; off += chunk) {
    uint8_t n = (uint8_t)min<uint16_t>(chunk, 256 - off);
    if (!memRead((uint8_t)off, out + off, n)) return false;
  }
  return true;
}



bool checkDevice(uint8_t addr) {
  i2c_cmd_handle_t cmd = i2c_cmd_link_create();
  i2c_master_start(cmd);
  i2c_master_write_byte(cmd, (addr << 1) | 0, true);  // 写入地址（写操作）
  i2c_master_stop(cmd);

  esp_err_t err = i2c_master_cmd_begin(I2C_PORT, cmd, pdMS_TO_TICKS(100));
  i2c_cmd_link_delete(cmd);

  return (err == ESP_OK);
}



// 切换页面
bool switchPage(uint8_t page) {
  Serial.printf("\n正在切换到 Page %d...\n", page);

  // 发送页面切换命令
  if (setPage((page == 1))) {
    delay(5);  // 等待切换完成
    int p = queryPageRPA();
    Serial.printf("After SPA%s, RPA=%d\n", page ? "1" : "0", p);
    return true;
  } else {
    Serial.println("✗ 页面切换命令发送失败");
    return false;
  }
}

// 读取当前页面
void readCurrentPage() {
  static uint8_t page[256];
  int currentPage = queryPageRPA();
  Serial.printf("当前page:%d\n", currentPage);
  if (currentPage == 0) {
    bool ok0 = readPage256(false, page, 32);
    Serial.printf("Page0 %s\n", ok0 ? "OK" : "FAIL");
  } else {
    bool ok1 = readPage256(true, page, 32);
    Serial.printf("Page1 %s\n", ok1 ? "OK" : "FAIL");
  }
}

// 读取当前页面信息
void showCurrentPage() {
  Serial.printf("\n=== 当前状态 ===\n");
  Serial.printf("I2C地址: 0x%02X\n", currentAddr);

  int currentPage = queryPageRPA();
  if (currentPage != 0xFF) {
    Serial.printf("实际页面: Page %d\n", currentPage);
  } else {
    Serial.printf("软件记录页面: Page %d (无法读取实际状态)\n", currentPage);
  }
  Serial.println("=================\n");
}

// 扫描I2C总线
void scanI2CBus() {
  Serial.println("\n扫描 I2C 总线...");
  Serial.println("    0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F");
  Serial.println("    -----------------------------------------------");

  int deviceCount = 0;

  for (uint8_t addr = 0x01; addr <= 0x7F; addr++) {
    if (addr % 16 == 0) {
      Serial.printf("%02X: ", addr & 0xF0);
    }

    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (addr << 1) | 0, true);
    i2c_master_stop(cmd);

    esp_err_t err = i2c_master_cmd_begin(I2C_PORT, cmd, pdMS_TO_TICKS(50));
    i2c_cmd_link_delete(cmd);

    if (err == ESP_OK) {
      Serial.printf("%02X ", addr);
      deviceCount++;
    } else {
      Serial.print("-- ");
    }

    if (addr % 16 == 15) {
      Serial.println();
    }
  }
  Serial.printf("\n找到 %d 个设备\n", deviceCount);
  Serial.printf("当前N34C04 I2C地址: 0x%02X\n", currentAddr);
}

void softReset() {
  Serial.println("系统正在重启...");
  delay(100);     // 等待串口输出完成
  esp_restart();  // 立即重启
}

// 读取数据
bool readData(uint8_t* buffer, uint16_t length) {
  // 从当前地址连续读取数据
  uint16_t offset = 0;
  // 每次读取32字节
  const uint8_t chunkSize = 32;

  while (offset < length) {
    uint8_t readSize = (uint8_t)min<uint16_t>(chunkSize, length - offset);
     // 注意：N34C04只有256字节页面
    uint8_t wordAddr = (uint8_t)(offset & 0xFF);

    if (!memRead(wordAddr, buffer + offset, readSize)) {
      Serial.printf("读取失败 at offset %u\n", offset);
      return false;
    }

    offset += readSize;
    // 给EEPROM一点时间
    delay(5);
  }
  return true;
}

// 读取所有页面（Page0和Page1）
void readAllPages() {
  Serial.println("\n=== 读取所有页面 ===");

  uint8_t allData[512];

  // 读取Page0
  if (!setPage(false)) {
    Serial.println("切换到Page0失败");
    return;
  }
  delay(5);

  if (!readPage256(false, allData, 32)) {
    Serial.println("读取Page0失败");
    return;
  }

  // 读取Page1
  if (!setPage(true)) {
    Serial.println("切换到Page1失败");
    return;
  }
  delay(5);

  if (!readPage256(true, allData + 256, 32)) {
    Serial.println("读取Page1失败");
    return;
  }

  Serial.println("\n所有数据:");
  hexDump(allData, 512, 0x0000);
  Serial.printf("成功读取全部数据: 512 字节\n");
}


// 读取指定页面
void readSpecificPage(int page) {
  if (page != 0 && page != 1) {
    Serial.println("页面必须是0或1");
    return;
  }

  uint8_t data[256];
  if (readPage256(page == 1, data, 32)) {
    Serial.printf("Page%d 数据:\n", page);
    hexDump(data, 256, 0x0000);
    Serial.printf("Page%d 读取成功\n", page);
  } else {
    Serial.printf("Page%d 读取失败\n", page);
  }
}

// 写入字节（单字节写入）
static bool memWriteByte(uint8_t wordAddr, uint8_t data) {
  i2c_cmd_handle_t cmd = i2c_cmd_link_create();

  i2c_master_start(cmd);
  i2c_master_write_byte(cmd, MEM_W_8B, true);
  i2c_master_write_byte(cmd, wordAddr, true);
  i2c_master_write_byte(cmd, data, true);
  i2c_master_stop(cmd);

  esp_err_t err = i2c_master_cmd_begin(I2C_PORT, cmd, pdMS_TO_TICKS(100));
  i2c_cmd_link_delete(cmd);

  if (err != ESP_OK) {
    Serial.printf("memWriteByte addr=0x%02X data=0x%02X err=%s\n", wordAddr, data, esp_err_to_name(err));
    return false;
  }
  // EEPROM写入时间（典型5ms）
  delay(10);
  return true;
}

// 页面写入（支持页写入优化）
static bool writePage(uint8_t page, const uint8_t* data, uint16_t offset, uint16_t length) {
  if (offset + length > PAGE_SIZE) {
    Serial.println("写入超出页面边界");
    return false;
  }

  // 切换到目标页面
  if (!setPage(page == 1)) {
    Serial.println("页面切换失败");
    return false;
  }

  // N34C04支持页写入（最多16字节），但为了简单，使用单字节写入
  for (uint16_t i = 0; i < length; i++) {
    if (!memWriteByte((uint8_t)(offset + i), data[i])) {
      Serial.printf("写入失败 at offset %u\n", offset + i);
      return false;
    }
  }

  return true;
}

// 写入数据
bool writeData(uint8_t* data, uint16_t length) {
  if (length > PAGE_SIZE) {
    Serial.printf("数据长度 %d 超过页面大小 %d\n", length, PAGE_SIZE);
    return false;
  }

  int currentPageState = queryPageRPA();
  if (currentPageState < 0) {
    Serial.println("无法获取当前页面状态");
    return false;
  }

  Serial.printf("写入到 Page %d, 起始地址 0x00, 长度 %d 字节\n", currentPageState, length);

  bool success = writePage(currentPageState, data, 0, length);

  if (success) {
    Serial.println("数据写入成功");
    // 验证写入
    uint8_t verify[256];
    if (readPage256(currentPageState == 1, verify, 32)) {
      Serial.println("验证读取:");
      hexDump(verify, length, 0);

      // 比较数据
      bool match = true;
      for (uint16_t i = 0; i < length; i++) {
        if (verify[i] != data[i]) {
          Serial.printf("验证失败 at offset %u: 期望 0x%02X, 实际 0x%02X\n",
                        i, data[i], verify[i]);
          match = false;
        }
      }

      if (match) {
        Serial.println("✓ 数据验证通过");
      } else {
        Serial.println("✗ 数据验证失败");
      }
    }
  }
  return success;
}

// 写入数据到当前页面
bool writeDataToCurrentPage(uint8_t* data, uint16_t length) {
  if (length > PAGE_SIZE) {
    Serial.printf("数据长度 %d 超过页面大小 %d\n", length, PAGE_SIZE);
    return false;
  }

  int currentPageState = queryPageRPA();
  if (currentPageState < 0) {
    Serial.println("无法获取当前页面状态");
    return false;
  }

  Serial.printf("写入到 Page %d, 起始地址 0x00, 长度 %d 字节\n", currentPageState, length);

  bool success = writePage(currentPageState, data, 0, length);

  if (success) {
    Serial.println("数据写入成功");
    // 验证写入
    uint8_t verify[256];
    if (readPage256(currentPageState == 1, verify, 32)) {
      bool match = true;
      for (uint16_t i = 0; i < length; i++) {
        if (verify[i] != data[i]) {
          Serial.printf("验证失败 at offset %u: 期望 0x%02X, 实际 0x%02X\n",  i, data[i], verify[i]);
          match = false;
        }
      }

      if (match) {
        Serial.println("✓ 数据验证通过");
        return true;
      } else {
        Serial.println("✗ 数据验证失败");
        return false;
      }
    }
  }
  return false;
}

// 写入数据到指定页面
bool writeDataToPage(int page, uint8_t* data, uint16_t length) {
  if (page != 0 && page != 1) {
    Serial.println("页面必须是0或1");
    return false;
  }

  if (length > PAGE_SIZE) {
    Serial.printf("数据长度 %d 超过页面大小 %d\n", length, PAGE_SIZE);
    return false;
  }

  Serial.printf("写入到 Page %d, 长度 %d 字节\n", page, length);

  bool success = writePage(page, data, 0, length);

  if (success) {
    Serial.println("数据写入成功");
    // 验证写入
    uint8_t verify[256];
    if (readPage256(page == 1, verify, 32)) {
      bool match = true;
      for (uint16_t i = 0; i < length; i++) {
        if (verify[i] != data[i]) {
          Serial.printf("验证失败 at offset %u: 期望 0x%02X, 实际 0x%02X\n",  i, data[i], verify[i]);
          match = false;
        }
      }

      if (match) {
        Serial.println("✓ 数据验证通过");
        return true;
      } else {
        Serial.println("✗ 数据验证失败");
        return false;
      }
    }
  }

  return false;
}


// 写入测试数据
void writeTestData() {

  Serial.println("写入数据模式: 0x00, 0x01, 0x02, ... 0xFF");
  int currentPageState = queryPageRPA();
  Serial.printf("\n=== 写入测试数据到 Page %d (I2C地址0x%02X) ===\n", currentPageState, currentAddr);
  if (currentPageState < 0) {
    Serial.println("无法获取当前页面状态，取消写入");
    return;
  }

  Serial.printf("\n=== 写入测试数据到 Page %d ===\n", currentPageState);
  Serial.println("写入数据模式: 0x00, 0x01, 0x02, ... 0xFF");

  // 准备测试数据
  uint8_t testData[256];
  for (int i = 0; i < 256; i++) {
    testData[i] = (uint8_t)(i & 0xFF);
  }

  // 写入数据
  if (writeData(testData, 256)) {
    Serial.println("测试数据写入完成");
  } else {
    Serial.println("测试数据写入失败");
  }
}


// 接收二进制数据
void startDataReceive() {
  receivingData = true;
  rxBufferIndex = 0;
  Serial.println("READY_TO_RECEIVE");
}

void receiveDataByte(uint8_t data) {
  if (rxBufferIndex < MAX_DATA_SIZE) {
    rxBuffer[rxBufferIndex++] = data;
  }
}

void endDataReceive() {
  receivingData = false;

  if (rxBufferIndex == 0) {
    Serial.println("ERROR: No data received");
    return;
  }

  Serial.printf("Received %d bytes of data\n", rxBufferIndex);

  // 根据数据长度决定写入方式
  if (rxBufferIndex == 512) {
    // 写入两个页面
    Serial.println("Writing to both pages...");
    bool success0 = writeDataToPage(0, rxBuffer, 256);
    bool success1 = writeDataToPage(1, rxBuffer + 256, 256);

    if (success0 && success1) {
      Serial.println("SUCCESS: Both pages written");
    } else {
      Serial.println("ERROR: Failed to write");
    }
  } else if (rxBufferIndex == 256) {
    // 写入当前页面
    Serial.println("Writing to current page...");
    if (writeDataToCurrentPage(rxBuffer, 256)) {
      Serial.println("SUCCESS: Data written to current page");
    } else {
      Serial.println("ERROR: Failed to write to current page");
    }
  } else {
    Serial.printf("ERROR: Unsupported data length: %d (expected 256 or 512)\n", rxBufferIndex);
  }
}

void checkN34c04(){
  if (checkDevice(N34C04_BASE_ADDR)) {
    Serial.printf("N34C04设备检测成功\n");
  } else {
    Serial.printf("N34C04设备检测失败\n");
  }
}

void showHelp() {
  Serial.println("\n========================================");
  Serial.println("可用命令:");
  Serial.println("========================================");
  Serial.println("  READ      - 读取当前页面数据");
  Serial.println("  READ_ALL  - 读取所有页面(Page0+Page1)");
  Serial.println("  READ_P0   - 读取Page0");
  Serial.println("  READ_P1   - 读取Page1");
  Serial.println("  WRITE     - 写入测试数据(0x00-0xFF)到当前页面");
  Serial.println("  PAGE0     - 切换到Page 0");
  Serial.println("  PAGE1     - 切换到Page 1");
  Serial.println("  STATUS    - 显示当前状态和页面");
  Serial.println("  SCAN      - 扫描I2C总线");
  Serial.println("  RESTART   - 软件重启");
  Serial.println("  HELP      - 显示帮助");
  Serial.println("========================================\n");
  Serial.println("二进制数据传输命令:");
  Serial.println("  SEND_256  - 准备接收256字节数据");
  Serial.println("  SEND_512  - 准备接收512字节数据");
  Serial.println("========================================\n");
}


void processCommand(String cmd) {
  if (cmd == "READ") {
    readCurrentPage();
  } else if (cmd == "READ_ALL") {
    readAllPages();
  } else if (cmd == "READ_P0") {
    readSpecificPage(0);
  } else if (cmd == "READ_P1") {
    readSpecificPage(1);
  } else if (cmd == "WRITE") {
    writeTestData();
  } else if (cmd == "PAGE0") {
    switchPage(0);
  } else if (cmd == "PAGE1") {
    switchPage(1);
  } else if (cmd == "STATUS") {
    showCurrentPage();
  } else if (cmd == "SCAN") {
    scanI2CBus();
  } else if (cmd == "HELP") {
    showHelp();
  } else if (cmd == "RESTART") {
    softReset();
  } else if (cmd == "SEND_256") {
    startDataReceive();
  } else if (cmd == "SEND_512") {
    startDataReceive();
  } else if (cmd == "CHECK_N34C04") {
    checkN34c04();
  } else if (cmd.length() > 0) {
    Serial.printf("未知命令: %s\n", cmd.c_str());
    Serial.println("输入 HELP 查看可用命令");
  }
}
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=========================================");
  Serial.println("N34C04 Dual Page EEPROM Access");
  Serial.println("=========================================\n");

  // 初始化I2C
  conf.mode = I2C_MODE_MASTER;
  conf.sda_io_num = PIN_SDA;
  conf.scl_io_num = PIN_SCL;
  conf.sda_pullup_en = GPIO_PULLUP_ENABLE;  // 建议仍然加外部上拉
  conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
  conf.master.clk_speed = I2C_FREQ;

  esp_err_t err;
  err = i2c_param_config(I2C_PORT, &conf);
  Serial.printf("[I2C] param_config: %s (%d)\n", esp_err_to_name(err), (int)err);
  if (err != ESP_OK) return;

  err = i2c_driver_install(I2C_PORT, conf.mode, 0, 0, 0);
  Serial.printf("[I2C] driver_install: %s (%d)\n", esp_err_to_name(err), (int)err);
  if (err != ESP_OK) return;

  // 检测设备
  if (checkDevice(N34C04_BASE_ADDR)) {
    Serial.printf("✓ N34C04设备 (0x%02X) 已检测到\n", N34C04_BASE_ADDR);
  } else {
    Serial.printf("✗ 未检测到设备 (地址0x%02X)\n", N34C04_BASE_ADDR);
  }
  // showHelp();
}

void loop() {
  // 处理二进制数据接收
  if (receivingData) {
    while (Serial.available()) {
      uint8_t data = Serial.read();
      receiveDataByte(data);
      // 检查是否接收完成
      if (rxBufferIndex >= MAX_DATA_SIZE) {
        endDataReceive();
        break;
      }
    }
  }

  // 处理文本命令
  if (Serial.available() && !receivingData) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    input.toUpperCase();
    processCommand(input);
  }
}
