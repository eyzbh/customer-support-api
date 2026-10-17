
from rag_service import answer_question


question = "I forgot my password. How can I get back into my account?"

result = answer_question(question)

print("\nQuestion:", result["question"])
print("\nAnswer:", result["answer"])
print("\nSources:")

for source in result["sources"]:
    print(f"- {source['title']} (similarity: {source['score']})")
    print(f"  {source['content']}")
