import os
import sys

print("=== 脚本开始执行 ===")
print(f"当前目录: {os.getcwd()}")
print(f"文件列表: {os.listdir('.')}")

try:
    print("尝试导入 jmcomic...")
    from jmcomic import *
    print("jmcomic 导入成功")
except Exception as e:
    print(f"导入失败: {e}")
    sys.exit(1)

try:
    print("尝试导入 prepare_actions_input_and_secrets...")
    from workflow_export_favorites import prepare_actions_input_and_secrets
    print("导入成功")
except Exception as e:
    print(f"导入失败: {e}")
    sys.exit(1)


def prepare_actions_input_and_secrets():
    """
    本函数替代对配置文件中的 ${} 的解析函数
    目的是为了支持：当没有配置环境变量时，可以找另一个环境变量来用
    """

    def env(match: Match) -> str:
        name = match[1]
        value = os.getenv(name, '')

        # 配置了有效的值，放行
        if value != '':
            return value

        # 未配置，或者值为空（值为空是GitHub Actions的未配置默认值）
        # 是EMAIL相关，也放行
        if name.startswith('EMAIL'):
            return value

        # 尝试从工作流中取
        value = os.getenv(f'IN_{name}', '')
        # 工作流也没有传值
        ExceptionTool.require_true(value != '', f'未配置secrets或工作流，字段为: {name}')

        return value

    JmcomicText.dsl_replacer.add_dsl_and_replacer(r'\$\{(.*?)\}', env)


def main():
    print("=== 进入 main 函数 ===")
    prepare_actions_input_and_secrets()
    print("prepare_actions_input_and_secrets 执行完成")
    # 关闭logging，保证安全
    disable_jm_log()
    print("准备读取配置文件...")
    
    # 打印当前目录，确认配置文件路径
    print(f"当前目录: {os.getcwd()}")
    print(f"../assets/option/ 目录内容: {os.listdir('../assets/option/') if os.path.exists('../assets/option/') else '目录不存在'}")
    
    option = create_option('../assets/option/option_workflow_export_favorites.yml')
    print("配置文件读取成功")
    print("开始执行插件...")
    option.call_all_plugin('main', safe=False)
    print("=== 脚本执行完成 ===")


if __name__ == '__main__':
    main()
