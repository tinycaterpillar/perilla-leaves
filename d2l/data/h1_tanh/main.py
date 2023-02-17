from torch import nn, cuda
import torch
import torch.nn.functional as F
import os
import pathlib

class Net(nn.Module):
    """MLP with 1 hidden layer with tanh activate function"""
    def __init__(self):
        super(Net, self).__init__()
        self.l1 = nn.Linear(2, 128)
        self.l2 = nn.Linear(128, 1)

    def forward(self, x):
        x = torch.tanh(self.l1(x))
        return self.l2(x)

device = "cuda" if cuda.is_available() else "cpu"
cur_path = str(pathlib.Path(__file__).parent.resolve())
model = Net()

print(model.__doc__)
print(model)

model.load_state_dict(torch.load(cur_path + "/weight/20000_weight.pth", map_location=device))
print("load weight complete")