from torch import nn, cuda
import torch
import torch.nn.functional as F
import os
import pathlib

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.l1 = nn.Linear(2, 1)

    def forward(self, x):
        return self.l1(x)

device = "cuda" if cuda.is_available() else "cpu"
cur_path = str(pathlib.Path(__file__).parent.resolve())
model = Net()
model.to(device)

model.load_state_dict(torch.load(cur_path + "/weight.pth", map_location=device))
print("load weight complete")

