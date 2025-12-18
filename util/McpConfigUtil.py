import yaml
import os


class ConfigUtil:
    def __init__(self):
        pass

    @staticmethod
    def load_model_path_from_config(config_path):
        """从YAML配置文件中加载模型路径"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
                    model_path = config.get('model', {}).get('path')
                    if model_path:
                        # 规范化路径分隔符
                        model_path = model_path.replace('\\', '/')
                    print(f"从配置文件加载模型路径: {model_path}")
                    return model_path
            else:
                print(f"配置文件不存在: {config_path}")
                return None
        except yaml.YAMLError as e:
            print(f"YAML格式错误: {e}")
            return None
        except Exception as e:
            print(f"配置文件读取失败: {e}")
            return None

    @staticmethod
    def load_chroma_save_path_from_config(config_path):
        """从YAML配置文件中加载模型路径"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
                    chroma_save_path = config.get('chroma', {}).get('save_path')
                    if chroma_save_path:
                        # 规范化路径分隔符
                        chroma_save_path = chroma_save_path.replace('\\', '/')
                    print(f"从配置文件加载模型路径: {chroma_save_path}")
                    return chroma_save_path
            else:
                print(f"配置文件不存在: {config_path}")
                return None
        except yaml.YAMLError as e:
            print(f"YAML格式错误: {e}")
            return None
        except Exception as e:
            print(f"配置文件读取失败: {e}")
            return None