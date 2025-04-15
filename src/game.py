"""
海龟汤游戏主类模块
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from colorama import init, Fore, Style

from src.game_controller import GameController
from src.state_schema import GameState
from src.context import GameContext

# 初始化colorama以支持彩色输出
init()

class TurtleSoupGame:
    """海龟汤游戏主类"""
    
    def __init__(
        self,
        controller: GameController,
        context: GameContext,
        log_file: str = "game.log",
        save_file: Optional[str] = None
    ):
        """
        初始化游戏
        
        Args:
            controller: 游戏流程控制器
            context: 游戏上下文（包含故事、答案等）
            log_file: 日志文件路径
            save_file: 存档文件路径
        """
        self.controller = controller
        self.context = context
        self.save_file = save_file
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def _print_welcome(self):
        """打印欢迎信息"""
        print(f"\n{Fore.CYAN}欢迎来到海龟汤！{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}🎭 故事背景：{Style.RESET_ALL}")
        print(self.context.story)
        print("\n你可以通过提问来推理真相。每个问题我都会回答\"是\"、\"否\"或\"无关\"。")
        print("输入 'hint' 获取提示，输入 'answer' 查看答案，输入 'quit' 退出游戏。")
        print(f"提示次数限制：{self.context.max_hints}次，回合数限制：{self.context.max_rounds}回合")
    
    def _process_input(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            
        Returns:
            Optional[Dict[str, Any]]: 处理后的状态，如果是特殊命令则返回None
        """
        self.logger.info("[用户输入] %s", user_input)
        
        # 处理特殊命令
        if user_input.lower() == 'quit':
            self._handle_game_end()
            return None
        elif user_input.lower() == 'hint':
            if self.context.hint_count >= self.context.max_hints:
                print(f"\n{Fore.RED}❌ 提示次数已用完！{Style.RESET_ALL}")
                return None
            print(f"\n{Fore.GREEN}💡 提示：{Style.RESET_ALL}")
            # TODO: 实现提示生成
            return None
        elif user_input.lower() == 'answer':
            self._handle_game_end()
            print(f"\n{Fore.RED}🔍 真相：{Style.RESET_ALL}")
            print(self.context.answer)
            return None
            
        # 创建游戏状态
        return self._create_state(user_input)
    
    def _create_state(self, question: str) -> Dict[str, Any]:
        """
        创建当前回合状态
        
        Args:
            question: 玩家问题
            
        Returns:
            Dict[str, Any]: 游戏状态
        """
        state_data = {
            "current_question": question
        }
        #同步当前问题
        state_data["current_question"] = question
        #同步当前brain_chain
        state_data["brain_chain"] = self.context.brain_chain


        # 同步当前链ID
        if self.context.brain_chain and self.context.brain_chain.current_chain_id:
            state_data["current_chain_id"] = self.context.brain_chain.current_chain_id 
        return GameState(**state_data)
    
    def _print_game_status(self, state: Dict[str, Any]):
        """
        打印游戏状态
        
        Args:
            state: 游戏状态
        """
        print(f"\n{Fore.CYAN}🧠 当前状态回顾{Style.RESET_ALL}")
        print(f"👀 玩家提问：{state['current_question']}")
        print(f"🎯 回复内容：{state['current_host_reply']}")
        
        # 显示状态标记
        if state.get("is_deviated"):
            print(f"{Fore.RED}🌀 状态：偏离主线{Style.RESET_ALL}")
        elif state.get("is_looping"):
            print(f"{Fore.YELLOW}🔄 状态：正在绕圈{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✨ 状态：推理正常{Style.RESET_ALL}")
            
        # 显示回合信息
        print(f"\n📊 当前回合：{self.context.current_round}/{self.context.max_rounds}")
        print(f"💡 剩余提示：{self.context.max_hints - self.context.hint_count}次")
            
        # 记录日志
        self.logger.info("[状态更新] 问题: %s, 回复: %s, 偏离: %s, 循环: %s",
                        state['current_question'],
                        state['current_host_reply'],
                        state.get('is_deviated', False),
                        state.get('is_looping', False))
    
    def _handle_game_end(self):
        """处理游戏结束"""
        # 计算得分
        score = self.context.calculate_score()
        analysis = self.context.generate_final_analysis()
        
        # 打印结果
        print(f"\n{Fore.YELLOW}🎮 游戏结束！{Style.RESET_ALL}")
        print(f"✨ 最终得分：{score}")
        print(f"📝 评语：{analysis}")
        
        # 保存存档
        if self.save_file:
            self.context.save_to_file(self.save_file)
            print(f"\n💾 游戏记录已保存至：{self.save_file}")
    
    async def run(self):
        """运行游戏主循环"""
        self._print_welcome()
        
        while True:
            try:
                # 检查回合数限制
                if self.context.current_round >= self.context.max_rounds:
                    print(f"\n{Fore.RED}❌ 已达到最大回合数限制！{Style.RESET_ALL}")
                    self._handle_game_end()
                    break
                
                # 获取用户输入
                user_input = input(f"\n{Fore.GREEN}请输入你的问题：{Style.RESET_ALL}")
                
                # 处理输入
                current_state = self._process_input(user_input)
                if current_state is None:  # 特殊命令处理
                    if user_input.lower() == 'quit':
                        break
                    continue
                
                # 运行游戏流程
                try:
                    result_state = await self.controller.process_question(user_input)
                    self._print_game_status(result_state)
                    
                    # 更新上下文
                    self.context.update_from_state(GameState(**result_state))
                    
                except Exception as e:
                    self.logger.error("流程图执行错误：%s", str(e))
                    print(f"\n{Fore.RED}❌ 抱歉，处理您的问题时出现错误。请重试。{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}游戏被中断。感谢游玩！{Style.RESET_ALL}")
                self._handle_game_end()
                break
            except Exception as e:
                self.logger.error("游戏运行错误：%s", str(e))
                print(f"\n{Fore.RED}❌ 发生错误：{str(e)}{Style.RESET_ALL}")
                self._handle_game_end()
                break

def main():
    """游戏入口函数"""
    # 创建游戏实例
    game = TurtleSoupGame(
        controller=GameController(...),  # 需要传入必要的agent
        context=GameContext(...),  # 需要传入故事和答案
        save_file="game_save.json"  # 存档文件
    )
    
    # 运行游戏
    asyncio.run(game.run()) 