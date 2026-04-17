"""
详细参数选项卡
展示并允许编辑所有 SPD 参数
"""
import json
from pickle import FALSE

import customtkinter as ctk
from typing import Optional, Dict, Any

from ..widgets.editable_field import EditableField
from ...core.model import SPDDataModel, DataChangeEvent
from ...core.parser import DDR4Parser
from ...core.parser.manufacturers import COMMON_MANUFACTURERS, get_manufacturer_id
from ...utils.constants import Colors, SPD_BYTES, MODULE_TYPES, MTB, DIE_DENSITY_SELECT, BANK_GROUPS_SELECT, \
    BANK_PER_GROUPS_SELECT, COL_BITS_SELECT, ROW_BITS_SELECT, DIE_COUNT_SELECT, PACKAGE_TYPE_SELECT, RANK_COUNT_SELECT, \
    RANK_MIX_SELECT, DEVICE_WIDTH_SELECT, MEMORY_ORG_BUS_WIDTH_SELECT, TOTAL_BUS_WIDTH_SELECT, ADDRESS_MAPPING_SELECT


class DetailsTab(ctk.CTkFrame):
    """详细参数选项卡"""

    def __init__(self, master, data_model: SPDDataModel, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.data_model = data_model
        self.fields = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._setup_ui()
        self.data_model.add_observer(self._on_data_changed)

    def _setup_ui(self):
        """设置UI - 两列布局"""
        # 可滚动区域
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        # 配置两列等宽布局
        self.scroll_frame.grid_columnconfigure(0, weight=1, uniform="col")
        self.scroll_frame.grid_columnconfigure(1, weight=1, uniform="col")

        # 当前行索引（用于跟踪每列的位置）
        self._left_row = 0
        self._right_row = 0

        # 左列分组
        self._create_section("基本信息", [
            ("内存类型", "memory_type", "text", False),
            ("模组类型", "module_type", "select", True, list(MODULE_TYPES.values())),
            ("容量", "capacity", "text", False),
            ("组织结构", "organization", "text", False),
            # ("总线宽度", "bus_width", "text", False),
            ("速度等级", "speed_grade", "number", True, 1600, 5000),
            ("电压", "voltage", "text", False),
            ("温度传感器", "thermal_sensor", "text", True),

        ], column=0)

        self._create_section("SPD 元数据", [
            ("SPD 字节使用", "spd_bytes_used", "text", False),
            ("SPD 修订版", "spd_revision", "text", False),
        ], column=0)

        self._create_section("内存组织", [
            ("总线宽度", "total_bus_width", "select", True,TOTAL_BUS_WIDTH_SELECT),
            ("主数据宽度", "primary_bus_width", "text", False),
            ("ECC 支持", "ecc_support", "text", False),
            ("ECC 宽度", "ecc_width", "text", False),
            ("Rank 类型", "rank_mix", "select", True,RANK_MIX_SELECT),  # 对称/非对称
            ("Rank 数量", "rank_count", "select", True,RANK_COUNT_SELECT),
            ("颗粒位宽", "device_width", "select", True,DEVICE_WIDTH_SELECT),  # x4/x8/x16
            ("模组位宽", "memory_org_bus_width", "text", True,MEMORY_ORG_BUS_WIDTH_SELECT),  # 64位/72位
            ("颗粒总数", "total_devices", "text", False),
            ("地址映射", "address_mapping", "select", True,ADDRESS_MAPPING_SELECT),
        ], column=0)

        # 右列分组
        self._create_section("制造商信息", [
            ("制造商", "manufacturer", "select", True, COMMON_MANUFACTURERS),
            ("部件号", "part_number", "text", True),
            ("序列号", "serial_number", "hex", True, None, None, True),
            ("生产日期", "manufacturing_date", "text", True),
        ], column=1)


        self._create_section("其他信息", [
            ("CRC校验(126,127)", "block0_crc", "text", False),
            ("CRC校验(254,255)", "block1_crc", "text", False),
        ], column=1)

        self._create_section("DRAM 信息", [
            ("DRAM 制造商", "dram_manufacturer", "text", True),
            ("封装类型", "package_type", "select", True,PACKAGE_TYPE_SELECT),
            ("Die 密度", "die_density","select", True,DIE_DENSITY_SELECT),
            ("Die 数量", "die_count", "select", True,DIE_COUNT_SELECT),
            ("Die 组织", "die_organization", "text", False),
            ("行地址位", "row_bits", "select", True,ROW_BITS_SELECT),
            ("列地址位", "col_bits", "select", True,COL_BITS_SELECT),
            ("页大小", "page_size", "text", False),
            ("Bank 组数", "bank_groups", "select", True,BANK_GROUPS_SELECT),
            ("每组 Bank 数", "banks_per_group", "select", True,BANK_PER_GROUPS_SELECT),
        ], column=1)
    def _create_section(self, title: str, fields: list, column: int = 0):
        """创建一个参数分组

        Args:
            title: 分组标题
            fields: 字段配置列表
            column: 放置的列（0=左列, 1=右列）
        """
        # 获取当前列的行索引
        if column == 0:
            row = self._left_row
            self._left_row += 1
        else:
            row = self._right_row
            self._right_row += 1

        # 分组容器
        section_frame = ctk.CTkFrame(self.scroll_frame, fg_color=Colors.CARD_BG, corner_radius=10)
        section_frame.grid(row=row, column=column, sticky="nsew", padx=(0, 8) if column == 0 else (8, 0), pady=(0, 15))
        section_frame.grid_columnconfigure(0, weight=1)

        # 标题
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=("Arial", 14, "bold"),
            text_color=Colors.TEXT
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        # 分隔线
        separator = ctk.CTkFrame(section_frame, height=1, fg_color=Colors.SECONDARY)
        separator.grid(row=1, column=0, sticky="ew", padx=15)

        # 字段
        for i, field_config in enumerate(fields):
            name = field_config[0]
            key = field_config[1]
            field_type = field_config[2]
            editable = field_config[3] if len(field_config) > 3 else False

            options = None
            min_val = None
            max_val = None
            show_serial_generator = False

            if field_type == "select" and len(field_config) > 4:
                options = field_config[4]
            elif field_type == "number" and len(field_config) > 5:
                min_val = field_config[4]
                max_val = field_config[5]
            elif field_type == "hex" and len(field_config) > 6:
                # For hex fields, check if show_serial_generator flag is present
                show_serial_generator = field_config[6]

            field = EditableField(
                section_frame,
                label=name,
                value="-",
                field_type=field_type,
                options=options,
                min_value=min_val,
                max_value=max_val,
                editable=editable,
                on_change=lambda n, v, k=key: self._on_field_changed(k, v),
                show_serial_generator=show_serial_generator
            )
            field.grid(row=i + 2, column=0, sticky="ew", padx=15, pady=5)
            self.fields[key] = field

        # 底部间距
        ctk.CTkFrame(section_frame, height=10, fg_color="transparent").grid(
            row=len(fields) + 2, column=0
        )

    def _on_data_changed(self, event: DataChangeEvent):
        """数据变更回调"""
        self.refresh()

    def _on_field_changed(self, key: str, value: str):
        """字段变更回调"""
        print(f"[DEBUG DetailsTab] _on_field_changed called: key='{key}', value='{value}'")
        if not self.data_model.has_data:
            print(f"[DEBUG DetailsTab] No data in model, returning early")
            return

        print(f"[DEBUG DetailsTab] Processing field change: key={key}, value={value}")

        # 根据字段类型更新 SPD 数据
        if key == "manufacturer":
            # 更新制造商 ID
            first_byte, second_byte = get_manufacturer_id(value)
            print(f"[DEBUG] Manufacturer ID: first_byte=0x{first_byte:02X}, second_byte=0x{second_byte:02X}")
            # 移除不必要的条件检查，始终更新
            self.data_model.set_byte(SPD_BYTES.MANUFACTURER_ID_FIRST, first_byte)
            self.data_model.set_byte(SPD_BYTES.MANUFACTURER_ID_SECOND, second_byte)
            print(f"[DEBUG] Updated manufacturer bytes at {SPD_BYTES.MANUFACTURER_ID_FIRST} and {SPD_BYTES.MANUFACTURER_ID_SECOND}")

        elif key == "part_number":
            # 更新部件号 (20 字符，右侧填充空格)
            part_number = value.ljust(20)[:20]
            for i, char in enumerate(part_number):
                offset = SPD_BYTES.PART_NUMBER_START + i
                self.data_model.set_byte(offset, ord(char))

        elif key == "serial_number":
            # 更新序列号 (4 字节十六进制)
            try:
                hex_str = value.replace("0x", "").replace("0X", "").replace(" ", "")
                if len(hex_str) <= 8:
                    hex_str = hex_str.zfill(8)
                    for i in range(4):
                        byte_val = int(hex_str[i*2:(i+1)*2], 16)
                        self.data_model.set_byte(SPD_BYTES.SERIAL_NUMBER_1 + i, byte_val)
            except ValueError:
                pass

        elif key == "manufacturing_date":
            # 更新生产日期 (格式: YYYY-WXX 或 WXX/YYYY)
            try:
                # 尝试解析各种格式
                value = value.strip()
                year = None
                week = None

                if "/" in value:
                    # 格式: W26/2023 或 26/2023
                    parts = value.split("/")
                    week_part = parts[0].replace("W", "").replace("w", "")
                    week = int(week_part)
                    year = int(parts[1]) % 100  # 取后两位
                elif "-W" in value.upper():
                    # 格式: 2023-W26
                    parts = value.upper().split("-W")
                    year = int(parts[0]) % 100
                    week = int(parts[1])
                elif len(value) == 4 and value.isdigit():
                    # 只有年份
                    year = int(value) % 100
                    week = 1

                if year is not None:
                    self.data_model.set_byte(SPD_BYTES.MANUFACTURING_YEAR, year)
                if week is not None:
                    self.data_model.set_byte(SPD_BYTES.MANUFACTURING_WEEK, week)
            except (ValueError, IndexError):
                pass

        elif key == "module_type":
            # 更新模组类型
            for type_code, type_name in MODULE_TYPES.items():
                if type_name == value:
                    self.data_model.set_byte(SPD_BYTES.MODULE_TYPE, type_code)
                    break

        elif key == "speed_grade":
            # 更新速度等级 (通过修改 tCK_min)
            # 速度等级 = 2000000 / tCK_min (ps)
            # tCK_min = 2000000 / speed_grade
            try:
                speed = int(value)
                if speed == 1600:
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN, 0x0A)
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN_FTB, 0x00)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX, 0x0C)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX_FTB, 0x00)
                elif speed == 1866:
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN,  0x09)
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN_FTB,  0xCA)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX, 0x0C)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX_FTB, 0x00)
                elif speed == 2133:
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN, 0x08)
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN_FTB,  0xC1)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX, 0x0C)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX_FTB, 0x00)
                elif speed == 2400:
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN, 0x07)
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN_FTB,   0xD6)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX, 0x0C)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX_FTB, 0x00)
                elif speed == 2666:
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN,  0x06)
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN_FTB, 0x00)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX, 0x00)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX_FTB, 0x00)
                elif speed == 3200:
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN, 0x05)
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN_FTB, 0x00)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX, 0x00)
                    self.data_model.set_byte(SPD_BYTES.TCK_MAX_FTB, 0x00)
                elif 1600 <= speed <= 5000:
                    # tCK_min in ps, MTB = 125ps
                    tck_ps = 2000000 / speed
                    tck_ps_int = int(round(tck_ps))

                    tck_mtb = int(tck_ps_int // MTB)
                    tck_ftb = int(tck_ps_int - tck_mtb * MTB)  # 0..124

                    self.data_model.set_byte(SPD_BYTES.TCK_MIN, tck_mtb)
                    self.data_model.set_byte(SPD_BYTES.TCK_MIN_FTB, tck_ftb & 0xFF)
            except ValueError:
                pass
        #内存组织
        elif key == "total_bus_width":
            if value == '64 bits':
                self.data_model.set_byte(SPD_BYTES.BUS_WIDTH, 0x03)
            else:
                self.data_model.set_byte(SPD_BYTES.BUS_WIDTH, 0x0b)
        elif key == "rank_count":
            rank_count = int(value)
            org_byte = self.data_model.get_byte(SPD_BYTES.MODULE_ORG)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            new_bits_5_3 = rank_count - 1
            # 清除原来的 Bits 5~3 (位掩码: ~(0x07 << 3))
            org_byte &= ~(0x07 << 3)  # 清除位 3,4,5
            # 设置新的 Bits 5~3
            org_byte |= (new_bits_5_3 << 3)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            # self.data_model.set_byte(SPD_BYTES.BUS_WIDTH, org_byte)
            self.data_model.set_byte(SPD_BYTES.MODULE_ORG,org_byte)
        elif key == "rank_mix":
            org_byte = self.data_model.get_byte(SPD_BYTES.MODULE_ORG)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            # 清除原来的 Bit 6 (位掩码: ~(1 << 6))
            org_byte &= ~(1 << 6)  # 清除位 6
            # 设置新的 Bit 6
            rank_mix_value = 0 if value == 'Symmetrical' else 1
            org_byte |= (rank_mix_value << 6)
            self.data_model.set_byte(SPD_BYTES.MODULE_ORG, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "device_width":
            device_width = int(value)
            width_map = {
                4: 0,  # 000
                8: 1,  # 001
                16: 2,  # 010
                32: 3  # 011
            }
            org_byte = self.data_model.get_byte(SPD_BYTES.MODULE_ORG)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            # 清除原来的 Bits 2~0 (位掩码: ~0x07)
            org_byte &= ~0x07  # 清除位 0,1,2
            # 设置新的 Bits 2~0
            org_byte |= width_map[device_width]
            self.data_model.set_byte(SPD_BYTES.MODULE_ORG, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "package_type":
            org_byte = self.data_model.get_byte(SPD_BYTES.PACKAGE_TYPE)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            org_byte &= ~(1 << 7)  # 清除位 7
            # 设置新的 Bit 6
            rank_mix_value = 0 if value == 'Monolithic' else 1
            org_byte |= (rank_mix_value << 7)
            self.data_model.set_byte(SPD_BYTES.PACKAGE_TYPE, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "die_count":
            die_count = int(value)
            org_byte = self.data_model.get_byte(SPD_BYTES.PACKAGE_TYPE)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            # 清除 Bits 6~4
            org_byte &= ~(0x07 << 4)
            # 设置新的 Bit 6
            # 设置新的 Bits 6~4
            org_byte |= ((die_count - 1) << 4)
            self.data_model.set_byte(SPD_BYTES.PACKAGE_TYPE, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "row_bits":
            row_bits = int(value)
            org_byte = self.data_model.get_byte(SPD_BYTES.ADDRESSING)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            row_map = {
                12: 0,  # 000
                13: 1,  # 001
                14: 2,  # 010
                15: 3,  # 011
                16: 4,  # 100
                17: 5,  # 101
                18: 6  # 110
            }
            org_byte &= ~(0x07 << 3)  # 清除位 3,4,5
            # 设置新的 Bits 5~3
            org_byte |= (row_map.get(row_bits) << 3)
            # 确保 Bits 7~6 为 0 (Reserved)
            org_byte &= ~(0x03 << 6)
            self.data_model.set_byte(SPD_BYTES.ADDRESSING, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "col_bits":
            col_bits = int(value)
            org_byte = self.data_model.get_byte(SPD_BYTES.ADDRESSING)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            col_map = {
                9: 0,  # 000
                10: 1,  # 001
                11: 2,  # 010
                12: 3  # 011
            }
            # 清除原来的 Bits 2~0 (位掩码: ~0x07)
            org_byte &= ~0x07  # 清除位 0,1,2
            # 设置新的 Bits 2~0
            org_byte |= col_map.get(col_bits)
            # 确保 Bits 7~6 为 0 (Reserved)
            org_byte &= ~(0x03 << 6)
            self.data_model.set_byte(SPD_BYTES.ADDRESSING, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "bank_groups":
            bank_groups = int(value)
            org_byte = self.data_model.get_byte(SPD_BYTES.DENSITY_BANKS)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            bank_groups_map = {
                0: 0,  # 00 - no bank groups
                2: 1,  # 01 - 2 bank groups
                4: 2,  # 10 - 4 bank groups
            }
            bits_7_6  = bank_groups_map.get(bank_groups)
            print(bank_groups_map.get(bank_groups))
            # 清除原来的Bits 7~6 (位掩码: ~(0x03 << 6))
            org_byte &= ~(0x03 << 6)  # 清除位 6,7
            # 设置新的Bits 7~6
            org_byte |= (bits_7_6 << 6)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            self.data_model.set_byte(SPD_BYTES.DENSITY_BANKS, org_byte)
        elif key == "banks_per_group":
            banks_per_group = int(value)
            org_byte = self.data_model.get_byte(SPD_BYTES.DENSITY_BANKS)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            bank_address_map = {
                4: 0,  # 00 - 4 banks
                8: 1,  # 01 - 8 banks
            }
            bits_5_4=bank_address_map.get(banks_per_group)
            # 清除原来的Bits 5~4 (位掩码: ~(0x03 << 4))
            org_byte &= ~(0x03 << 4)  # 清除位 4,5
            # 设置新的Bits 5~4
            org_byte |= (bits_5_4 << 4)
            self.data_model.set_byte(SPD_BYTES.DENSITY_BANKS, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "die_density":
            org_byte = self.data_model.get_byte(SPD_BYTES.DENSITY_BANKS)
            print(f"[DEBUG] MODULE_ORG byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
            # 清除原来的Bits 3~0 (位掩码: ~0x0F)
            org_byte &= ~0x0F  # 清除位 0-3
            capacity_map = {
                '256Mb': 0,  # 0000
                '512Mb': 1,  # 0001
                '1Gb' :2,  # 0010 - 1Gb
                '2Gb' :3,  # 0011 - 2Gb
                '4Gb' :4,  # 0100 - 4Gb
                '8Gb' :5,  # 0101 - 8Gb
                '16Gb': 6,  # 0110 - 16Gb
                '32Gb': 7,  # 0111 - 32Gb
                '12Gb': 8,  # 1000 - 12Gb
                '24Gb': 9,  # 1001 - 24Gb
            }
            # 设置新的Bits 3~0
            org_byte |= capacity_map.get(value)
            self.data_model.set_byte(SPD_BYTES.DENSITY_BANKS, org_byte)
            print(f"[DEBUG] MODULE_NEW byte: 0x{org_byte:02X} (binary: {org_byte:08b})")
        elif key == "address_mapping":
            if value == 'standard':
                self.data_model.set_byte(SPD_BYTES.ADDRESS_MAPPING, 0x00)
            else:
                self.data_model.set_byte(SPD_BYTES.ADDRESS_MAPPING, 0x01)



    def refresh(self):
        """刷新显示"""
        print("[DEBUG DetailsTab] refresh() called")
        if not self.data_model.has_data:
            self._show_no_data()
            return

        parser = DDR4Parser(self.data_model.data)
        info = parser.to_dict()
        if "error" in info:
            self._show_no_data()
            return
        spd_block0_crc = self.data_model.verify_spd_crc(0,SPD_BYTES.BOCK0_CRC_MSB,SPD_BYTES.BOCK0_CRC_LSB)
        spd_block1_crc = self.data_model.verify_spd_crc(128,SPD_BYTES.BOCK1_CRC_MSB,SPD_BYTES.BOCK1_CRC_LSB)

        # 更新字段值
        #DRAM制造商
        dram_mfr = info.get("dram_manufacturer", {})
        #内存组织
        memory_org = info.get("memory_organization", {})

        ecc_info = memory_org.get("ecc_info", {})
        capacity = memory_org.get("capacity", {})
        address_mapping = memory_org.get("address_mapping", 0)
        # 温度传感器
        thermal = memory_org.get("thermal_sensor", {})
        #颗粒信息
        particle_info = info.get("particle_info", {})
        bank_config = particle_info.get("bank_config", {})
        die_info = particle_info.get("die_info", {})
        addressing = particle_info.get("addressing", {})

        field_mapping = {
            #基本信息
            "memory_type": info.get("memory_type", "-"),
            "module_type": info.get("module_type", "-"),
            "capacity": info.get("capacity", "-"),
            "organization": info.get("organization", "-"),
            "bus_width": f"{info.get('capacity_details', {}).get('bus_width', '-')} bit",
            "speed_grade": str(info.get("speed_grade", "-")),
            "voltage": f"{info.get('voltage', 1.2):.1f}V",
            #制造商信息
            "manufacturer": info.get("manufacturer", "-"),
            "part_number": info.get("part_number", "-"),
            "serial_number": info.get("serial_number", "-"),
            "manufacturing_date": info.get("manufacturing_date", "-"),
            #spd元数据
            "spd_bytes_used": f"{self.data_model.data[0]} bytes" if self.data_model.has_data else "-",
            "spd_revision": f"{self.data_model.data[1] >> 4}.{self.data_model.data[1] & 0x0F}" if self.data_model.has_data else "-",
            #other
            "block0_crc": "OK" if spd_block0_crc.get("is_valid") else "ERR",
            "block1_crc": "OK" if spd_block1_crc.get("is_valid") else "ERR",
            # 内存组织
            "total_bus_width": f"{ecc_info.get('total_width', '-')} bits",
            "primary_bus_width": f"{ecc_info.get('primary_width', '-')} bits",
            "ecc_support": f"{ecc_info.get('has_ecc', '-')}",
            "ecc_width": f"{ecc_info.get('extension_width', '-')} bits",
            "rank_count": memory_org.get("rank_count", 0),
            "rank_mix": "Symmetrical" if memory_org.get("rank_mix", 0) == 0  else "Asymmetrical",
            "device_width": memory_org.get("device_width", "-"),
            "memory_org_bus_width":  f"{memory_org.get("bus_width", "-")} bit",
            "total_devices": memory_org.get("total_devices", "-"),
            "thermal_sensor": thermal.get("description", "-"),
            "address_mapping": "standard" if address_mapping == 0 else "mirror",
            # DRAM 信息
            "dram_manufacturer": dram_mfr.get("name", "-"),
            "die_density": f"{die_info.get('density_gb', '-')} Gb",
            "die_count": str(die_info.get("die_count", "-")),
            "package_type": die_info.get("package_type", "-"),
            "die_organization": die_info.get("organization", "-"),
            "row_bits": str(addressing.get("row_bits", "-")),
            "col_bits": str(addressing.get("col_bits", "-")),
            "page_size": addressing.get("page_size_str", "-"),
            "bank_groups": str(bank_config.get("bank_groups", "-")),
            "banks_per_group": str(bank_config.get("banks_per_group", "-")),
            "total_banks": str(bank_config.get("total_banks", "-")),

        }

        print(f"[DEBUG DetailsTab] Updating fields with: manufacturer={field_mapping['manufacturer']}, module_type={field_mapping['module_type']}")

        for key, value in field_mapping.items():
            if key in self.fields:
                self.fields[key].set_value(str(value))

    def _show_no_data(self):
        """显示无数据状态"""
        for field in self.fields.values():
            field.set_value("-")
