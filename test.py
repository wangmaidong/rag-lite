from langchain_milvus import Milvus
from langchain_huggingface import HuggingFaceEmbeddings
import pymilvus
import asyncio
async def init_milvus_async():
    embeddings = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2',
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings":True}
    )
    URI = "http://49.235.139.52:19530"
    # 获取或者创建向量存储对象
    vectorstore = Milvus(
        embedding_function=embeddings,
        connection_args={
            "uri": URI
        },
    )
    return vectorstore


vectorstore = asyncio.run(init_milvus_async())
print(vectorstore)

# 先测试基本连接
# try:
#     # 直接使用 pymilvus 测试连接
#     connections = pymilvus.connections
#     connections.connect(
#         alias="default",
#         host='49.235.139.52',
#         port='19530'
#     )
#     print("连接成功")
#     connections.disconnect("default")
# except Exception as e:
#     print(f"连接失败: {e}")


