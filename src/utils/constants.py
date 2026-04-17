"""
SPDTools 常量定义
"""

# HID 设备配置
DEFAULT_VID = 0x1A86
DEFAULT_PID = 0x5512

# SPD 数据大小
SPD_SIZE = 512
SPD_PAGE_SIZE = 256

# DDR4 SPD 字节偏移定义
class SPD_BYTES:
    # 基本信息 (0-127)
    BYTES_USED = 0  # SPD 使用的字节数 (0x000)
    REVISION = 1  # SPD 修订版本 (0x001)
    DRAM_TYPE = 2  # DRAM 设备类型 (0x002, 0x0C = DDR4)
    MODULE_TYPE = 3  # 模块类型 (0x003)
    DENSITY_BANKS = 4  # 密度和 Bank 组 (0x004)
    ADDRESSING = 5  # 行列地址位数 (0x005)
    PACKAGE_TYPE = 6  # 封装类型 (0x006)
    OPTIONAL_FEATURES = 7  # 可选功能 (0x007)
    THERMAL_REFRESH = 8  # 热刷新选项 (0x008)
    OTHER_OPTIONAL = 9  # 其他可选功能 (0x009)
    SECONDARY_PACKAGE = 10  # 次要封装类型 (0x00A)
    VOLTAGE = 11  # 模块标称电压 (0x00B)
    MODULE_ORG = 12  # 模块组织 (0x00C)
    BUS_WIDTH = 13  # 模块内存总线宽度 (0x00D)
    THERMAL_SENSOR = 14  # 温度传感器 (0x00E)
    EXTENDED_MODULE_TYPE = 15  # 扩展模块类型 (0x00F)  ← 新增，之前遗漏

    # 时序参数
    TIMEBASES = 17  # 时间基准 (0x011)
    TCK_MIN = 18  # 最小时钟周期 (tCKAVGmin) (0x012)
    TCK_MAX = 19  # 最大时钟周期 (tCKAVGmax) (0x013)
    CAS_LATENCIES_1 = 20  # CAS 延迟支持 第一字节 (0x014)
    CAS_LATENCIES_2 = 21  # CAS 延迟支持 第二字节 (0x015)
    CAS_LATENCIES_3 = 22  # CAS 延迟支持 第三字节 (0x016)
    CAS_LATENCIES_4 = 23  # CAS 延迟支持 第四字节 (0x017)
    TAA_MIN = 24  # 最小 CAS 延迟时间 (tAAmin) (0x018)
    TRCD_MIN = 25  # 最小 RAS 到 CAS 延迟 (tRCDmin) (0x019)
    TRP_MIN = 26  # 最小行预充电时间 (tRPmin) (0x01A)
    TRAS_TRC_HIGH = 27  # tRASmin 和 tRCmin 高半字节 (0x01B)
    TRAS_MIN_LOW = 28  # 最小 Active 到 Precharge (tRASmin) 低位 (0x01C)
    TRC_MIN_LOW = 29  # 最小 Active 到 Active/Refresh (tRCmin) 低位 (0x01D)
    TRFC1_LOW = 30  # 最小刷新恢复时间 (tRFC1min) 低位 (0x01E)
    TRFC1_HIGH = 31  # tRFC1min 高位 (0x01F)
    TRFC2_LOW = 32  # tRFC2min 低位 (0x020)
    TRFC2_HIGH = 33  # tRFC2min 高位 (0x021)
    TRFC4_LOW = 34  # tRFC4min 低位 (0x022)
    TRFC4_HIGH = 35  # tRFC4min 高位 (0x023)
    TFAW_HIGH = 36  # tFAWmin 最高有效半字节 (0x024)
    TFAW_LOW = 37  # tFAWmin 最低有效字节 (0x025)
    TRRD_S_MIN = 38  # 最小 tRRD_Smin, 不同 bank 组 (0x026)
    TRRD_L_MIN = 39  # 最小 tRRD_Lmin, 相同 bank 组 (0x027)
    TCCD_L_MIN = 40  # 最小 tCCD_Lmin, 相同 bank 组 (0x028)
    TWR_MIN_HIGH = 41  # tWRmin 高位 (0x029)
    TWR_MIN_LOW = 42  # 最小写恢复时间 (tWRmin) 低位 (0x02A)
    TWTR_MIN_HIGH = 43  # tWTRmin 高位 (0x02B)
    TWTR_S_MIN = 44  # 最小写读到时间 (tWTR_Smin), 不同 bank 组 (0x02C)
    TWTR_L_MIN = 45  # 最小写读到时间 (tWTR_Lmin), 相同 bank 组 (0x02D)

    # 细粒度时序调整 (FTB) - 注意：这些都在 117-125 字节范围
    TCCD_L_MIN_FTB = 117  # tCCD_Lmin 微调偏移 (0x075)
    TRRD_L_MIN_FTB = 118  # tRRD_Lmin 微调偏移 (0x076)
    TRRD_S_MIN_FTB = 119  # tRRD_Smin 微调偏移 (0x077)
    TRC_MIN_FTB = 120  # tRCmin 微调偏移 (0x078)
    TRP_MIN_FTB = 121  # tRPmin 微调偏移 (0x079)
    TRCD_MIN_FTB = 122  # tRCDmin 微调偏移 (0x07A)
    TAA_MIN_FTB = 123  # tAAmin 微调偏移 (0x07B)
    TCK_MAX_FTB = 124  # tCKAVGmax 微调偏移 (0x07C)
    TCK_MIN_FTB = 125  # tCKAVGmin 微调偏移 (0x07D)

    # CRC 校验
    BOCK0_CRC_LSB = 126  # CRC 最低有效字节 (0x07E)
    BOCK0_CRC_MSB = 127  # CRC 最高有效字节 (0x07F)
    ADDRESS_MAPPING  = 131  # CRC 最高有效字节 (0x07F)

    BOCK1_CRC_LSB = 254  # CRC 最低有效字节 (0x07E)
    BOCK1_CRC_MSB = 255  # CRC 最高有效字节 (0x07F)
    # 制造商信息 (320-383)
    MANUFACTURER_ID_FIRST = 320   # 制造商 ID (第一字节)
    MANUFACTURER_ID_SECOND = 321  # 制造商 ID (第二字节)
    MANUFACTURING_LOCATION = 322  # 制造地点
    MANUFACTURING_YEAR = 323      # 制造年份
    MANUFACTURING_WEEK = 324      # 制造周
    SERIAL_NUMBER_1 = 325         # 序列号字节 1
    SERIAL_NUMBER_2 = 326         # 序列号字节 2
    SERIAL_NUMBER_3 = 327         # 序列号字节 3
    SERIAL_NUMBER_4 = 328         # 序列号字节 4
    PART_NUMBER_START = 329       # 部件号起始位置
    PART_NUMBER_END = 348         # 部件号结束位置 (20字符)
    REVISION_CODE = 349           # 修订代码

    # DRAM 制造商信息 (350-351，与模组制造商分离)
    DRAM_MANUFACTURER_ID_FIRST = 350   # DRAM 制造商 ID (第一字节)
    DRAM_MANUFACTURER_ID_SECOND = 351  # DRAM 制造商 ID (第二字节)

    # XMP 2.0 配置 (384-511)
    # 根据 XMP 2.0 规范
    # Byte 384-385: Intel XMP Identification String (0x0C, 0x4A/'J')
    XMP_HEADER = 384              # XMP 头部标识 (0x180)
    # Byte 386: XMP Organization / Profile Enable bits (bit0=Profile1, bit1=Profile2)
    XMP_PROFILE_ENABLED = 386     # Profile 启用状态
    # Byte 387: XMP Revision (e.g., 0x20 = XMP 2.0)
    XMP_REVISION = 387            # XMP 修订版本
    XMP_PROFILE1_START = 393      # XMP Profile 1 起始 (0x189)
    XMP_PROFILE2_START = 440      # XMP Profile 2 起始 (0x1B8)


# XMP 2.0 Profile 内部字段偏移 (相对于 XMP_PROFILE*_START)
# 说明：XMP Profile 的时序单位同样基于 DDR4 的 MTB/FTB (MTB=125ps, FTB=1ps)。
class XMP_PROFILE_OFFSETS:
    # 基础字段
    VDD_VOLTAGE = 0          # VDD 电压编码 (带 bit7 启用位)
    CAS_LATENCIES_0 = 4      # CAS Latencies Supported (bitmap, byte 0, CL7..)
    CAS_LATENCIES_1 = 5      # CAS Latencies Supported (bitmap, byte 1)
    CAS_LATENCIES_2 = 6      # CAS Latencies Supported (bitmap, byte 2)
    TCK_MTB = 3              # tCKAVGmin (MTB, 125ps)

    # 时序 MTB 字段
    TAA_MTB = 8              # tAAmin (MTB)
    TRCD_MTB = 9             # tRCDmin (MTB)
    TRP_MTB = 10             # tRPmin (MTB)
    TRAS_TRC_HIGH = 11       # tRAS/tRC 高位 nibble 组合
    TRAS_MTB_LOW = 12        # tRAS 低 8 位 (MTB)
    TRC_MTB_LOW = 13         # tRC 低 8 位 (MTB)

    # 进阶时序 (MTB, 与 DDR4 SPD Timing 字段布局基本一致)
    TRFC1_LOW = 14           # tRFC1 低位 (MTB)
    TRFC1_HIGH = 15          # tRFC1 高位 (MTB)
    TRFC2_LOW = 16           # tRFC2 低位 (MTB)
    TRFC2_HIGH = 17          # tRFC2 高位 (MTB)
    TRFC4_LOW = 18           # tRFC4 低位 (MTB)
    TRFC4_HIGH = 19          # tRFC4 高位 (MTB)

    TFAW_HIGH = 20           # tFAW 高位 (bits 11:8 in low nibble)
    TFAW_LOW = 21            # tFAW 低位
    TRRD_S_MIN = 22          # tRRD_S (MTB)
    TRRD_L_MIN = 23          # tRRD_L (MTB)
    TCCD_L_MIN = 24          # tCCD_L (MTB)
    TWR_HIGH = 25            # tWR 高位 (bits 11:8 in low nibble)
    TWR_LOW = 26             # tWR 低位
    TWTR_S_MIN = 27          # tWTR_S (MTB)
    TWTR_L_MIN = 28          # tWTR_L (MTB)

    # 细粒度时序调整 (FTB, signed int8, 1ps)
    # 这些偏移在实际 SPD 数据中位于 profile 尾部 (示例：0x1AB..0x1AF)。
    TRC_FTB = 34             # tRC Fine Offset
    TRP_FTB = 35             # tRP Fine Offset
    TRCD_FTB = 36            # tRCD Fine Offset
    TAA_FTB = 37             # tAA Fine Offset
    TCK_FTB = 38             # tCK Fine Offset

# DDR4 类型标识
DDR4_TYPE = 0x0C

# 模组类型映射
MODULE_TYPES = {
    0x01: "RDIMM",
    0x02: "UDIMM",
    0x03: "SO-DIMM",
    0x04: "LRDIMM",
    0x05: "Mini-RDIMM",
    0x06: "Mini-UDIMM",
    0x08: "72b-SO-RDIMM",
    0x09: "72b-SO-UDIMM",
    0x0C: "16b-SO-DIMM",
    0x0D: "32b-SO-DIMM",
}

# Bank 组数映射
BANK_GROUPS = {
    0b00: 4,
    0b01: 2,
}

# 密度映射 (Gb)
DENSITY_MAP = {
    0b0000: 0.256,
    0b0001: 0.512,
    0b0010: 1,
    0b0011: 2,
    0b0100: 4,
    0b0101: 8,
    0b0110: 16,
    0b0111: 32,
    0b1000: 12,
    0b1001: 24,
}

# 设备宽度映射
DEVICE_WIDTH = {
    0b000: 4,
    0b001: 8,
    0b010: 16,
    0b011: 32,
}

# 行地址位数映射
ROW_BITS = {
    0b000: 12,
    0b001: 13,
    0b010: 14,
    0b011: 15,
    0b100: 16,
    0b101: 17,
    0b110: 18,
}

# 列地址位数映射
COL_BITS = {
    0b000: 9,
    0b001: 10,
    0b010: 11,
    0b011: 12,
}

# 时间基准 (ps)
MTB = 125    # Medium Time Base = 125ps
FTB = 1      # Fine Time Base = 1ps

# 频率速度等级映射 (tCK -> MT/s)
# tCK ranges based on JEDEC standard:
# DDR4-3200: 625ps (1600MHz), DDR4-2933: 682ps (1466.5MHz), DDR4-2666: 750ps (1333MHz)
SPEED_GRADES = {
    (625, 682): 3200,    # DDR4-3200: tCK = 625ps
    (682, 750): 2933,    # DDR4-2933: tCK = 682ps (added - was missing!)
    (750, 833): 2666,    # DDR4-2666: tCK = 750ps
    (833, 938): 2400,    # DDR4-2400: tCK = 833ps
    (938, 1071): 2133,   # DDR4-2133: tCK = 938ps
    (1071, 1250): 1866,  # DDR4-1866: tCK = 1071ps
    (1250, 1500): 1600,  # DDR4-1600: tCK = 1250ps
}

# XMP 标识
XMP_MAGIC = 0x0C

# Package Type (Byte 6, bit 7)
PACKAGE_TYPES = {
    0: "Monolithic",
    1: "3DS (Non-Monolithic)"
}

# Die Count (Byte 6, bits 6:4)
DIE_COUNTS = {
    0: 1, 1: 2, 2: 3, 3: 4,
    4: 5, 5: 6, 6: 7, 7: 8
}

# Signal Loading (Byte 6, bits 1:0)
SIGNAL_LOADING = {
    0: "Not specified",
    1: "Multi-load stack",
    2: "Single-load stack (3DS)",
    3: "Reserved"
}

# Banks per bank group (DDR4 always has 4 banks per group)
# BANKS_PER_GROUP = 4

# UI 颜色主题
class Colors:
    PRIMARY = "#1f538d"
    SECONDARY = "#444444"
    SUCCESS = "#27ae60"
    WARNING = "#f39c12"
    DANGER = "#c0392b"
    DANGER_HOVER = "#e74c3c"
    BACKGROUND = "#2b2b2b"
    CARD_BG = "#363636"
    TEXT = "#ffffff"
    TEXT_SECONDARY = "#aaaaaa"
    MODIFIED = "#f1c40f"
    HIGHLIGHT = "#3498db"

# 常用制造商列表（用于下拉选择）
DIE_DENSITY_SELECT = [
    '256Mb',
    '512Mb',
    '1Gb',
    '2Gb',
    '4Gb',
    '8Gb',
    '12Gb',
    '16Gb',
    '24Gb',
    '32Gb',
]

BANK_GROUPS_SELECT = [
    "0",
    "2",
    "4",
]
BANK_PER_GROUPS_SELECT = [
    "4",
    "8",
]

ROW_BITS_SELECT = [
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18"
]

COL_BITS_SELECT = [
    "9",
    "10",
    "11",
    "12"
]

DIE_COUNT_SELECT = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
]

PACKAGE_TYPE_SELECT = {
    "Monolithic": 0,
    "Non-Monolithic": 1,
}

RANK_COUNT_SELECT = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
]

RANK_MIX_SELECT = [
    "Symmetrical",
    "Asymmetrical",
]

DEVICE_WIDTH_SELECT = [
    "4",
    "8",
    "16",
    "32",
]

MEMORY_ORG_BUS_WIDTH_SELECT=[
    "8","16","32","64"
]

TOTAL_BUS_WIDTH_SELECT=[
    "64 bits",
    "72 bits"
]

ADDRESS_MAPPING_SELECT=[
    "standard",
    "mirror"
]