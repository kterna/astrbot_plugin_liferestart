from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from .core.Life import Life
import random
import os

@register("liferestart", "AstrBot", "人生重开模拟器", "1.0.1")
class LifeRestartPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        try:
            Life.load(self.data_dir)
        except Exception as e:
            raise

    def genp(self, prop: int) -> dict:
        """生成属性值
        
        Args:
            prop (int): 总属性点数
            
        Returns:
            dict: 分配后的属性值字典
        """
        ps = []
        tmp = prop
        while True:
            for i in range(0, 4):
                if i == 3:
                    ps.append(tmp)
                else:
                    if tmp >= 10:
                        ps.append(random.randint(0, 10))
                    else:
                        ps.append(random.randint(0, tmp))
                tmp -= ps[-1]
            if ps[3] < 10:
                break
            else:
                tmp = prop
                ps.clear()
        return {
            'CHR': ps[0],  # 颜值
            'INT': ps[1],  # 智力
            'STR': ps[2],  # 体质
            'MNY': ps[3]   # 家境
        }

    @filter.command("人生重开帮助", alias=['重开帮助'])
    async def help(self, event: AstrMessageEvent):
        """显示人生重开模拟器帮助信息"""
        help_text = """人生重开模拟器使用帮助
================================

【基础指令】
--------------------------------
• /人生重来：开始新的人生
• /重开：开始新的人生（简写）

【注意事项】
--------------------------------
1. 每次重开都会随机生成不同的天赋和属性
2. 属性包括：颜值、智力、体质、家境
3. 游戏过程会显示人生重要事件
4. 最后会生成人生总结报告

祝你玩得开心！
================================"""
        url = await self.text_to_image(help_text)
        yield event.image_result(url)

    @filter.command("重开", alias=['人生重来'])
    async def remake(self, event: AstrMessageEvent):
        """开始新的人生"""
        try:
            life = None
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    life = Life()
                    life.setTalentHandler(lambda ts: random.choice(ts).id)
                    life.setPropertyhandler(self.genp)
                    if life.choose():
                        break
                    retry_count += 1
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise Exception("多次尝试初始化生命失败")

            if not life:
                yield event.plain_result("初始化人生失败，请稍后再试")
                return

            name = event.get_sender_name()
            
            all_text = """你的命运正在重启....
================================\n\n"""
            
            all_text += f"""{name}本次重生的基本信息如下：

【你的天赋】
--------------------------------\n"""
            for i, t in enumerate(life.talent.talents, 1):
                all_text += f"{i}. 天赋：【{t.name}】\n   效果：{t.desc}\n\n"

            all_text += """【基础属性】
--------------------------------
"""
            all_text += f"""颜值：{life.property.CHR}
智力：{life.property.INT}
体质：{life.property.STR}
家境：{life.property.MNY}

"""

            all_text += """【人生经历】
================================\n"""
            res = life.run()
            all_text += '\n\n'.join('\n'.join(x) for x in res)
            all_text += "\n\n"

            all_text += """【人生总结】
================================\n"""
            all_text += life.property.gensummary()
            all_text += "\n================================"

            url = await self.text_to_image(all_text)
            yield event.image_result(url)

        except Exception as e:
            error_msg = f"发生错误：{str(e)}"
            yield event.plain_result(error_msg)

    @filter.command("人生重开开", alias=["人生重开关"])
    async def handle_plugin_switch(self, event: AstrMessageEvent):
        """处理插件开关命令"""
        message = event.message_str.strip()
        group_id = str(event.message_obj.group_id)
        
        enabled = message == "人生重开开"
        await self.set_group_enabled(group_id, enabled)
        
        yield event.plain_result(f"已{'启用' if enabled else '禁用'}人生重开模拟器")
