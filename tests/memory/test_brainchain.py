""" 测试 BrainChainMemory 单元测试 (已通过)"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import patch
from src.memory.brainchain import BrainChainMemory, BrainChain, BrainNode

@pytest.fixture
def memory():
    """创建测试用的 BrainChainMemory 实例"""
    return BrainChainMemory()

@pytest.fixture
def mock_time():
    """Mock time.time() 函数"""
    with patch('time.time', return_value=1000.0) as mock:
        yield mock

@pytest.fixture
def mock_uuid():
    """Mock uuid.uuid4() 函数"""
    with patch('uuid.uuid4', return_value='test-uuid') as mock:
        yield mock

@pytest.fixture
def mock_logger():
    """Mock logger 对象"""
    with patch('src.memory.brainchain.logger') as mock:
        yield mock

class TestBrainChainMemory:
    """BrainChainMemory 单元测试"""
    
    def test_create_chain(self, memory, mock_time, mock_uuid):
        """测试创建新思维链"""
        chain_id = memory.create_chain()
        assert chain_id == 'test-uuid'
        assert chain_id in memory.brainchains
        assert isinstance(memory.brainchains[chain_id], BrainChain)
        assert memory.brainchains[chain_id].metadata['created_at'] == 1000.0
        assert memory.brainchains[chain_id].metadata['last_used_at'] == 1000.0
        assert memory.brainchains[chain_id].metadata['revisit_count'] == 0
    
    def test_add_node(self, memory, mock_time, mock_uuid):
        """测试添加节点到思维链"""
        chain_id = memory.create_chain()
        node_id = memory.add_node(
            content="测试问题",
            chain_id=chain_id,
            host_reply="测试回答",
            reply_type="yes",
            notes="测试备注"
        )
        
        assert node_id == 'test-uuid'
        chain = memory.get_chain(chain_id)
        node = chain.nodes[node_id]
        
        # 验证节点基本属性
        assert node.content == "测试问题"
        assert node.host_reply == "测试回答"
        assert node.timestamp == 1000.0
        assert node.reply_type == "yes"
        assert node.notes == "测试备注"
        
        # 验证父子关系
        assert node.parent_id is None  # 根节点
        assert len(node.children_ids) == 0  # 暂无子节点
        
        # 添加子节点并验证关系
        child_id = memory.add_node(
            content="子节点",
            chain_id=chain_id,
            parent_id=node_id,
            host_reply="子节点回答",
            reply_type="no",
            notes="子节点备注"
        )
        child_node = chain.nodes[child_id]
        assert child_node.parent_id == node_id
        assert child_id in node.children_ids
    
    def test_save_context(self, memory, mock_logger):
        """测试保存上下文"""
        inputs = {"question": "测试问题"}
        outputs = {
            "answer": "测试回答",
            "reply_type": "no",
            "notes": "推理说明"
        }
        
        memory.save_context(inputs, outputs)
        
        # 验证节点是否正确创建
        chain = memory.get_chain(memory.current_chain_id)
        node = next(iter(chain.nodes.values()))
        assert node.content == "测试问题"
        assert node.host_reply == "测试回答"
        assert node.reply_type == "no"
        assert node.notes == "推理说明"
        
        # 验证日志记录
        mock_logger.info.assert_called_once()
    
    def test_load_memory_variables(self, memory):
        """测试加载记忆变量"""
        # 创建测试数据
        chain_id = memory.create_chain()
        memory.add_node(
            content="问题1",
            chain_id=chain_id,
            host_reply="回答1",
            reply_type="yes",
            notes="备注1"
        )
        memory.add_node(
            content="问题2",
            chain_id=chain_id,
            host_reply="回答2",
            reply_type="no",
            notes="备注2"
        )
        
        # 测试加载
        variables = memory.load_memory_variables({})
        content = variables[memory.memory_key]
        
        # 验证格式化输出
        assert "思维链" in content
        assert "问题1" in content
        assert "问题2" in content
        assert "回答1" in content
        assert "回答2" in content
        assert "备注1" in content
        assert "备注2" in content
    
    def test_metadata_updates(self, memory, mock_time):
        """测试元数据更新"""
        # 创建第一个思维链
        chain_id_1 = memory.create_chain()
        memory.add_node(
            content="问题1", 
            chain_id=chain_id_1,
            host_reply="回答1",
            reply_type="yes",
            notes="备注1"
        )
        
        # 创建第二个思维链
        chain_id_2 = memory.create_chain()
        memory.add_node(
            content="问题2", 
            chain_id=chain_id_2,
            host_reply="回答2",
            reply_type="no",
            notes="备注2"
        )
        
        # 验证初始状态
        chain_1 = memory.get_chain(chain_id_1)
        assert chain_1.metadata['revisit_count'] == 0
        
        # 从链2切换回链1，应该增加 revisit_count
        memory.add_node(
            content="问题3", 
            chain_id=chain_id_1,
            host_reply="回答3",
            reply_type="irrelevant",
            notes="备注3"
        )
        assert chain_1.metadata['revisit_count'] == 1
        
        # 在同一个链上继续添加节点不应增加 revisit_count
        memory.add_node(
            content="问题4", 
            chain_id=chain_id_1,
            host_reply="回答4",
            reply_type="yes",
            notes="备注4"
        )
        assert chain_1.metadata['revisit_count'] == 1
        
        # 测试最后使用时间更新
        mock_time.return_value = 2000.0
        memory.add_node(
            content="问题5", 
            chain_id=chain_id_1,
            host_reply="回答5",
            reply_type="no",
            notes="备注5"
        )
        assert chain_1.metadata['last_used_at'] == 2000.0
    
    def test_summarize_brainchains(self, memory):
        """测试思维链摘要生成"""
        # 创建测试数据
        chain_id = memory.create_chain()
        root_id = memory.add_node(
            content="根节点问题",
            chain_id=chain_id,
            host_reply="根节点回答",
            reply_type="yes",
            notes="根节点备注"
        )
        
        memory.add_node(
            content="子节点问题",
            chain_id=chain_id,
            parent_id=root_id,
            host_reply="子节点回答",
            reply_type="no",
            notes="子节点备注"
        )
        
        summary = memory.summarize_brainchains()
        
        # 验证摘要内容
        assert "🔮 思维链" in summary
        assert "创建时间" in summary
        assert "最近使用" in summary
        assert "被访问次数" in summary
        assert "根节点问题" in summary
        assert "根节点回答" in summary
        assert "子节点问题" in summary
        assert "子节点回答" in summary
        assert "根节点备注" in summary
        assert "子节点备注" in summary
    
    def test_invalid_operations(self, memory):
        """测试无效操作处理"""
        # 测试获取不存在的链
        assert memory.get_chain("invalid-id") is None
        
        # 测试向不存在的链添加节点
        node_id = memory.add_node(
            content="测试",
            host_reply="回答",
            reply_type="irrelevant",
            notes="备注"
        )  # 应该自动创建新链
        assert node_id is not None
        
        # 测试无效的 reply_type
        with pytest.raises(ValueError):
            memory.add_node(
                content="测试",
                reply_type="invalid"  # 只允许 yes/no/irrelevant
            )
    
    def test_clear(self, memory, mock_logger):
        """测试清除功能"""
        # 创建测试数据
        chain_id = memory.create_chain()
        memory.add_node(
            content="测试",
            chain_id=chain_id,
            host_reply="回答",
            reply_type="yes",
            notes="备注"
        )
        
        # 清除
        memory.clear()
        
        # 验证结果
        assert len(memory.brainchains) == 0
        assert memory.current_chain_id is None
        mock_logger.info.assert_called_with("清除所有思维链")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, memory):
        """测试并发操作"""
        import asyncio
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def concurrent_operation():
            try:
                yield
            finally:
                # 清理资源
                memory.clear()
        
        async def create_chain_and_nodes():
            chain_id = memory.create_chain()
            await asyncio.sleep(0.1)  # 模拟并发延迟
            memory.add_node(
                content="测试",
                chain_id=chain_id,
                host_reply="回答",
                reply_type="yes",
                notes="备注"
            )
            return chain_id
        
        async with concurrent_operation():
            # 并发创建多个链和节点
            tasks = [create_chain_and_nodes() for _ in range(5)]
            chain_ids = await asyncio.gather(*tasks)
            
            # 验证所有链都被正确创建
            assert len(set(chain_ids)) == 5  # 确保创建了5个不同的链
            for chain_id in chain_ids:
                chain = memory.get_chain(chain_id)
                assert len(chain.nodes) == 1  # 每个链应该有一个节点 