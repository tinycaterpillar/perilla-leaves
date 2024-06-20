import io
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.cm as cm
from scipy.fft import fft, fftfreq
from torchvision import transforms
from PIL import Image

class Fourier_obj:
    def __init__(self, val: list, dt: int, fs: int, nFFT: int):
        self.N = len(val) # total numbor of data
        self.val = np.array(val)
        self.dt = dt # gap of sampling time
        self.fs = fs # sampling frequency
        self.nFFT = nFFT # window size

    def __stft(self, ub=25000):
        if hasattr(self, 'focused_val'):
            cur_val = self.focused_val
            cur_FrameSize = self.FrameSize
        else:
            cur_val = self.val
            cur_FrameSize = self.N

        win = signal.windows.hann(self.nFFT)
        self.__SFT = signal.ShortTimeFFT(win=win, hop=1, fs=self.fs, scale_to='magnitude', phase_shift=0)
        zData = self.__SFT.stft(cur_val, p0=0, p1=cur_FrameSize)
        absZ = np.abs(zData)
        self.xData = np.arange(1, cur_FrameSize+1)*self.__SFT.delta_t
        yData = self.__SFT.f
        self.yData = yData[np.where(yData <= ub)]
        self.absZ = absZ[:self.yData.shape[0], :]

    def __colormap_config(self):
        if not hasattr(self, 'absZ'): raise RuntimeError("run __sftf before __colormap_config")

        colorMax, colorMin = self.absZ.max(), self.absZ.min()
        # Black #000000
        # magenta #c20078
        # Blue #0343df
        # Cyan #00ffff
        # Green #15b01a
        # yellow #ffff14
        # OrangeRed #fe420f
        # Red #e50000
        # White #ffffff
        colors = ['#000000', '#c20078', '#0343df', '#00ffff', '#15b01a', '#ffff14', '#fe420f', '#e50000', '#ffffff']
        self.norm = plt.Normalize(colorMin, colorMax)
        self.cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", colors)
        self.levels = [0, colorMin]
        for i in range(1, 8): self.levels.append(colorMin + i * (colorMax - colorMin) / 9)
        self.levels.append(colorMax)
        self.colormapping = cm.ScalarMappable(norm=self.norm, cmap=self.cmap)

    # Extract FrameSize number of elements around the point where the absolute value is greatest in val
    def focus(self, FrameSize=2000):
        self.FrameSize = FrameSize
        max_abs_idx = np.argmax(np.abs(self.val))
        start_idx = max_abs_idx - self.FrameSize//2
        end_idx = max_abs_idx + self.FrameSize//2
        if start_idx < 0:
            end_idx -= start_idx
            start_idx = 0
        elif end_idx >= self.N:
            start_idx -= end_idx-(self.N-1)
            end_idx = self.N-1
        if start_idx < 0: raise Exception("input data indexing error")
        self.focused_val = self.val[start_idx: end_idx]

    # return ai input data
    def get_verdict_data(self):
        if not hasattr(self, 'focused_val'): self.focus()
        if not hasattr(self, 'absZ'): self.__stft()
        if not hasattr(self, 'levels'): self.__colormap_config()

        fig = plt.figure(frameon=False)
        fig.set_size_inches(1, 1)
        plt.colorbar(self.colormapping, ax=plt.gca())
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        plt.contourf(self.xData, self.yData, self.absZ, levels=self.levels, cmap=self.cmap, norm=self.norm)

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        ret = Image.open(buf).convert('RGB')
        transform = transforms.Compose([
            transforms.Resize((300, 300)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        ret = transform(ret).unsqueeze(0)
        return ret

    def fft(self, fft_file_name="fft", ub=25000):
        yf = fft(self.val)
        xf = fftfreq(self.N, self.dt)[:self.N//2]
        idx = np.where(xf == ub)[0].item()
        y = 2.0/self.N * np.abs(yf[0:idx])
        print(f"save fft data as {fft_file_name}.bin")
        y.tofile(f"{fft_file_name}.bin")

    def analyze(self, stft_file_name = "", ub=25000):
        if not hasattr(self, 'absZ'): self.__stft(ub)
        if not hasattr(self, 'levels'): self.__colormap_config()

        if hasattr(self, 'focused_val'):
            cur_val = self.focused_val
            cur_FrameSize = self.FrameSize
        else:
            cur_val = self.val
            cur_FrameSize = self.N

        # plt.contourf
        margin = 0.09
        sz = 9
        fig, ax = plt.subplots(
            2, 3, gridspec_kw={"width_ratios": [0.9, 9, 0.1], "height_ratios": [9, 1]}
        )

        xD = self.absZ.sum(axis=1)
        xD.resize(self.nFFT)
        yD = np.arange(1, self.nFFT+1)*self.__SFT.delta_f
        ax[0,0].plot(xD, yD, color='green')
        ax[0,0].set_ylim([0, ub])
        ax[0,0].set_ylabel('Frequency(Hz)')

        contour = ax[0,1].contourf(self.xData, self.yData, self.absZ, levels=self.levels, cmap=self.cmap, norm=self.norm)
        ax[0,1].axis("off")

        t = np.arange(1, cur_FrameSize+1)*self.__SFT.delta_t
        ax[1,1].plot(t, cur_val, color='green')
        ax[1,1].set_xlabel('Time(Sec)')

        fig.delaxes(ax[1,0])
        fig.delaxes(ax[1,2])
        fig.set_figheight(sz)
        fig.set_figwidth(sz)

        cbar = fig.colorbar(contour, cax=ax[0, 2], orientation='vertical', spacing='proportional')
        plt.subplots_adjust(wspace=margin, hspace=margin)
        plt.tight_layout()
        if stft_file_name:
            print(f"save stft image as {stft_file_name}.png")
            plt.savefig(f'{stft_file_name}.png', dpi=400)
        else:
            plt.show()

    
        
