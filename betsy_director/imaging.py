import numpy as np

class ProcessedImage(object):
    IDENTITY_T = np.array([
        [ 1.0, 0.0, 0.0 ],
        [ 0.0, 1.0, 0.0 ],
        [ 0.0, 0.0, 1.0 ],
    ])

    # 12-bit full scale value
    PWM_FULL_SCALE = 0x0FFF

    def __init__(self, img, postscaler=1.0, gamma=2.4, transform=IDENTITY_T):
        self.img = img
        self.postscaler = postscaler
        self.gamma = gamma
        self.transform = transform
        self.processed = None

    @property
    def size(self):
        return self.img.size

    def process(self):
        if self.img.mode != 'RGB':
            self.img = self.img.convert('RGB')

        arr = np.asarray(self.img, dtype=np.uint8)

        # F: Range into [0, 1]
        postF = arr / 255.0

        # G: Apply gamma exponentiation
        postG = postF ** self.gamma

        # M: Apply channel transformation
        postM = postG.dot(self.transform)

        # P: Apply global post-scaler
        postM *= self.postscaler

        # C: Clamp to keep inside of [0, 1] range
        postC = np.clip(postM, 0.0, 1.0)

        # R: Range from [0, 1] into PWM full scale value
        postR = postC * self.PWM_FULL_SCALE

        self.processed = postR

    def crop2raw_bytes(self, xstart, ystart, xend, yend):
        box = self.processed[ystart:yend, xstart:xend]
        raw = box.astype(dtype=np.uint16).flatten('C').newbyteorder('B').tostring()
        return raw

def process_and_crop_image(image, cropmap, postscaler=1.0, gamma=2.4, transform=ProcessedImage.IDENTITY_T):
    pi = ProcessedImage(image, postscaler=postscaler, gamma=gamma, transform=transform)
    pi.process()

    for key, (xstart, ystart, xend, yend) in cropmap.items():
        yield key, pi.crop2raw_bytes(xstart, ystart, xend, yend)

