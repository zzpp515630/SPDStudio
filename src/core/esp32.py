import time
from datetime import datetime
from typing import List, Optional, Callable

import serial
import serial.tools.list_ports


class SerialDriver:
    def __init__(self, debug: bool = False, baudrate: int = 115200, timeout: float = 2.0):
        self._debug_log: List[str] = []
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.debug = debug

    def _log_debug(self, message: str):
        """记录调试日志"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        self._debug_log.append(log_entry)
        if self.debug:
            print(log_entry)

    def get_debug_log(self) -> str:
        """获取调试日志"""
        return "\n".join(self._debug_log)

    def clear_debug_log(self):
        """清除调试日志"""
        self._debug_log.clear()

    def enable_debug(self, enabled: bool = True):
        """启用/禁用调试模式"""
        self.debug = enabled

    @staticmethod
    def enumerate_devices() -> List[dict]:
        """枚举所有 HID 设备"""
        return []

    def connect(self, serial_port: str) -> bool:
        """连接串口"""
        try:
            self.serial = serial.Serial(
                port=serial_port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            time.sleep(0.1)  # 等待设备就绪
            print(f"✓ 成功连接到 {serial_port}")
            return True
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False

    def disconnect(self) -> None:
        """断开设备连接"""
        if self.serial:
            self._log_debug("断开设备连接")
            try:
                self.serial.close()
            except Exception as e:
                self._log_debug(f"断开连接时出错: {e}")
            self.serial = None

    def is_connected(self) -> bool:
        """检查设备是否已连接"""
        return self.serial is not None and self.serial.isOpen()

    def check_n34c04(self) -> bool:
        response = self.send_command("CHECK_N34C04", wait_time=0.1)
        if "N34C04设备检测成功" in response:
            return True
        elif "N34C04设备检测失败" in response:
            return False
        else:

            return False

    def read_spd(
        self,
        progress_callback: Optional[Callable[[float], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        set_status: Optional[Callable[[str], None]] = None,
    ) -> Optional[List[int]]:
        """
        读取完整的 512 字节 SPD 数据

        Args:
            progress_callback: 进度回调函数，参数为 0-1 的进度值
            log_callback: 日志回调函数

        Returns:
            512 字节的数据列表，失败返回 None
        """
        self._log_debug("开始读取 SPD 数据")
        response = self.send_command("READ_ALL", wait_time=0.1)
        if not response:
            print("✗ 读取失败：无响应")
            self._log_debug("✗ 读取失败：无响应")
            if log_callback:
                log_callback("✗ 读取失败：无响应")
            return None
        self._log_debug("开始解析 SPD 数据")
        if progress_callback:
            progress_callback(50)
        # 解析HEX数据
        data = self.parse_hex_dump(response)
        if progress_callback:
            progress_callback(99)
        if data and len(data) == 512:
            print(f"✓ 成功读取全部数据: {len(data)} 字节")
            self._log_debug(f"✓ 成功读取全部数据: {len(data)} 字节")
            if log_callback:
                log_callback(f"✓ 成功读取全部数据: {len(data)} 字节")
            return list(data)
        else:
            print(f"✗ 读取失败：数据长度不正确 ({len(data) if data else 0} 字节)")
            self._log_debug(f"✗ 读取失败：数据长度不正确 ({len(data) if data else 0} 字节)")
            if log_callback:
                log_callback(f"✗ 读取失败：数据长度不正确 ({len(data) if data else 0} 字节)")
            return None


    def write_spd(
        self,
        data: List[int],
        progress_callback: Optional[Callable[[float], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        set_status: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        写入 SPD 数据到内存条

        Args:
            data: 512 字节数据列表
            progress_callback: 进度回调函数
            log_callback: 日志回调函数

        Returns:
            是否写入成功
        """
        erase_data = b'\xFF' * 512
        self._log_debug("开始擦除...")
        if log_callback:
            log_callback(f"开始擦除...")
        if set_status:
            set_status("开始擦除...")
        success = self.send_binary_data_512(erase_data)
        if progress_callback:
            progress_callback(25)
        if success:
            if log_callback:
                log_callback("✓ 擦除完成！所有数据已设置为0xFF")
            # 可选：验证擦除结果
            read_data = self.read_all_pages()
            if read_data and read_data == erase_data:
                self._log_debug("✓ 擦除验证通过")
            else:
                self._log_debug("✗ 擦除验证失败")
                if log_callback:
                    log_callback(f"✗ 擦除验证失败")
                return False
        self._log_debug("开始写入...")
        if progress_callback:
            progress_callback(50)
        if log_callback:
            log_callback("开始写入...")
        if set_status:
            set_status("开始写入...")
        result =  self.send_binary_data_512(bytes(data))
        if result:
            self._log_debug("开始校验...")
            if progress_callback:
                progress_callback(75)
            if log_callback:
                log_callback("开始校验...")
            if set_status:
                set_status("开始校验...")
            result = self.verify_data(bytes(data))
            if result:
                self._log_debug("✓ 数据验证通过")
                return True
            else:
                self._log_debug("✗ 数据验证失败")
                if log_callback:
                    log_callback(f"✗ 数据验证失败")
                return False
        self._log_debug("✗ 写入失败")
        if log_callback:
            log_callback(f"✗ 写入失败")
        return False


    def send_command(self, cmd: str, wait_response: bool = True,
                     wait_time: float = 1.0, clear_buffer: bool = True) -> Optional[str]:
        """
        发送文本命令到ESP32

        Args:
            cmd: 命令字符串
            wait_response: 是否等待响应
            wait_time: 等待时间
            clear_buffer: 是否清空缓冲区

        Returns:
            响应内容，如果失败返回None
        """
        if not self.serial or not self.serial.is_open:
            print("串口未连接")
            return None

        try:
            if clear_buffer:
                # 清空缓冲区
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()

            # 发送命令
            self.serial.write(f"{cmd}\n".encode())
            self.serial.flush()

            if wait_response:
                time.sleep(wait_time)

                # 读取所有响应
                response = ""
                start_time = time.time()
                while time.time() - start_time < wait_time:
                    if self.serial.in_waiting:
                        response += self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                    time.sleep(0.05)

                return response.strip()

            return ""

        except Exception as e:
            print(f"发送命令失败: {e}")
            return None

    def send_binary_data_256(self, data: bytes) -> bool:
        """
        发送256字节二进制数据到ESP32

        Args:
            data: 要发送的数据（256字节）

        Returns:
            是否成功
        """
        if len(data) != 256:
            print(f"✗ 数据大小错误: {len(data)} 字节，需要 256 字节")
            return False

        # 发送准备命令
        response = self.send_command("SEND_256", wait_time=0.5, clear_buffer=True)

        if not response or "READY_TO_RECEIVE" not in response:
            print(f"✗ 未收到就绪信号: {response}")
            return False

        print(f"✓ 收到就绪信号，开始发送 256 字节数据...")

        try:
            # 发送二进制数据
            self.serial.write(data)
            self.serial.flush()

            # 等待写入完成响应
            response = self.wait_for_response(["OPERATION_COMPLETE", "OPERATION_FAILED"], timeout=5)

            if "✓ 数据验证通过" in response:
                print("✓ 数据发送并写入成功")
                return True
            elif "✗ 数据验证失败" in response:
                print(f"✗ 写入失败")
                return False
            else:
                print(f"✗ 未收到确认: {response}")
                return False

        except Exception as e:
            print(f"✗ 发送数据失败: {e}")
            return False

    def send_binary_data_512(self, data: bytes) -> bool:
        """
        发送512字节二进制数据到ESP32（分两次发送，每次256字节）

        Args:
            data: 要发送的数据（512字节）

        Returns:
            是否成功
        """
        if len(data) != 512:
            print(f"✗ 数据大小错误: {len(data)} 字节，需要 512 字节")
            return False

        print("开始分块发送512字节数据...")

        # 先切换到Page0
        print("切换到 Page 0...")
        if not self.switch_page(0):
            print("✗ 切换到 Page 0 失败")
            return False

        # 发送Page0数据（前256字节）
        print("发送 Page 0 数据...")
        if not self.send_binary_data_256(data[:256]):
            print("✗ Page 0 写入失败")
            return False

        time.sleep(0.5)  # 等待一下

        # 切换到Page1
        print("切换到 Page 1...")
        if not self.switch_page(1):
            print("✗ 切换到 Page 1 失败")
            return False

        # 发送Page1数据（后256字节）
        print("发送 Page 1 数据...")
        if not self.send_binary_data_256(data[256:]):
            print("✗ Page 1 写入失败")
            return False

        print("✓ 全部数据写入成功")
        return True

    def wait_for_response(self, expected_strings: List[str], timeout: float = 10.0) -> str:
        """
        等待特定响应字符串

        Args:
            expected_strings: 期望的响应字符串列表
            timeout: 超时时间（秒）

        Returns:
            接收到的响应内容
        """
        start_time = time.time()
        response = ""

        while time.time() - start_time < timeout:
            if self.serial.in_waiting:
                response += self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                print(f"response: {response}\n")
                for expected in expected_strings:
                    if expected in response:
                        return response
            time.sleep(0.1)

        return response

    @staticmethod
    def parse_hex_dump(text: str) -> Optional[bytes]:
        """
        解析HEX转储格式的数据

        Args:
            text: HEX转储文本

        Returns:
            解析后的数据
        """
        data = bytearray()
        in_data_section = False
        print(f"read{text}")
        for line in text.split('\n'):
            # 查找数据开始标记
            if "DATA_START" in line:
                in_data_section = True
                continue

            # 查找数据结束标记
            if "DATA_END" in line:
                break

            # 如果在数据段内，解析HEX数据
            if in_data_section and ':' in line and '\r' in line:
                # 提取地址后的部分
                parts = line.split(':', 1)
                if len(parts) == 2:
                    hex_part = parts[1].strip()
                    # 提取HEX字节
                    hex_bytes = hex_part.split()
                    for hex_byte in hex_bytes:
                        if len(hex_byte) == 2 and all(c in '0123456789ABCDEFabcdef' for c in hex_byte):
                            try:
                                data.append(int(hex_byte, 16))
                            except ValueError:
                                pass

        return bytes(data) if data else None

    def switch_page(self, page: int) -> bool:
        """切换页面"""
        cmd = "PAGE0" if page == 0 else "PAGE1"
        response = self.send_command(cmd, wait_time=1)

        if response and ("Switched to Page" in response or "RPA=" in response):
            print(f"✓ 切换到 Page {page}")
            return True
        else:
            print(f"✗ 切换 Page {page} 失败")
            return False

    def read_all_pages(self) -> Optional[bytes]:
        """读取所有页面（Page0+Page1）"""
        print("\n" + "=" * 50)
        print("开始读取所有页面...")
        print("=" * 50)

        response = self.send_command("READ_ALL", wait_time=0.1)
        if not response:
            print("✗ 读取失败：无响应")
            return None

        # 解析HEX数据
        data = self.parse_hex_dump(response)

        if data and len(data) == 512:
            print(f"✓ 成功读取全部数据: {len(data)} 字节")
            return data
        else:
            print(f"✗ 读取失败：数据长度不正确 ({len(data) if data else 0} 字节)")
            return None

    def verify_data(self, data: bytes) -> bool:
        """
        验证写入的数据

        Args:
            data: 原始数据（512字节）

        Returns:
            是否验证通过
        """
        print("\n" + "=" * 50)
        print("开始验证数据...")
        print("=" * 50)

        # 读取所有页面
        read_data = self.read_all_pages()
        if read_data is None:
            return False

        # 比较数据
        if read_data == data:
            print("\n✓ 数据验证通过！")
            return True
        else:
            print("\n✗ 数据验证失败！")

            # 显示差异
            diff_count = 0
            for i in range(len(data)):
                if read_data[i] != data[i]:
                    diff_count += 1
                    if diff_count <= 20:  # 只显示前20个差异
                        page = "Page0" if i < 256 else "Page1"
                        offset = i if i < 256 else i - 256
                        print(f"  {page}[{offset:3d}]: 期望 0x{data[i]:02X}, 实际 0x{read_data[i]:02X}")

            if diff_count > 20:
                print(f"  ... 还有 {diff_count - 20} 个差异")

            print(f"\n总差异数: {diff_count}")
            return False