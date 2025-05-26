
import torch 

def calculate_hyperbolic_tangent_difference(tensor1, tensor2):
    """ 
        Calculate the difference between two values with tanh.
    """
    return torch.tanh(torch.abs(tensor1) - torch.abs(tensor2)).sum() 

# Input data
test_data = [
    (torch.tensor([[0.0, 1.0, -1.0], [2.0, -2.0, 3.0]]), torch.tensor([[0.0, 1.0, -1.0], [-1.0, 2.0, 3.0]])),
    (torch.tensor([[1e10, 1e-10, -1e10], [2.5, -2.5, 0.0]]), torch.tensor([[1e10, 1e-10, -1e10], [2.0, -3.0, 0.0]])),
    (torch.tensor([[-1.0, -0.5, 0.0], [0.5, 1.0, 2.0]]), torch.tensor([[1.0, 0.5, 0.0], [0.0, -1.0, -2.0]]))
]

for tensor1, tensor2 in test_data:
    try:
        result = calculate_hyperbolic_tangent_difference(tensor1, tensor2)
        print(result)
    except Exception as e:
        print("error:", e)
