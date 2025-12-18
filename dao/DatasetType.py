from enum import Enum


class DatasetType(Enum):
    """
    数据集类型枚举类
    用于区分不同的数据来源或用途
    """
    CHROMA = "chroma"

    @classmethod
    def get_all_types(cls):
        """获取所有支持的数据集类型"""
        return [item.value for item in cls]

    @classmethod
    def is_valid_type(cls, dataset_type):
        """验证数据集类型是否有效"""
        return dataset_type in cls.get_all_types()
