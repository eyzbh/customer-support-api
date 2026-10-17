
from embedding_service import generate_embedding


text = "Customers can reset their passwords through the account recovery page."

vector = generate_embedding(text)

print("Vector type:", type(vector))
print("Vector dimensions:", len(vector))
print("First 10 values:", vector[:10])
