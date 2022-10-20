import cv2
import numpy as np
from sklearn.cluster import KMeans
import urllib.request
import ssl
import certifi


class ColorFinder:
    def __init__(self) -> None:
        pass

    def _make_bar(self, height, width, color):
        """
        Create an image of a given color
        :param: height of the image
        :param: width of the image
        :param: BGR pixel values of the color
        :return: tuple of bar, rgb values, and hsv values
        """
        bar = np.zeros((height, width, 3), np.uint8)
        bar[:] = color
        red, green, blue = int(color[2]), int(color[1]), int(color[0])
        hsv_bar = cv2.cvtColor(bar, cv2.COLOR_BGR2HSV)

        hue, sat, val = hsv_bar[0][0]
        if val <= 150:
            val = 150
        hsv_bar[0][0] = hue, sat, val
        rgb = cv2.cvtColor(hsv_bar, cv2.COLOR_HSV2RGB)
        red, green, blue = rgb[0][0]
        return bar, (red, green, blue), (hue, sat, val)

    def _make_histogram(self, cluster):
        """
        Count the number of pixels in each cluster
        :param: KMeans cluster
        :return: numpy histogram
        """
        numLabels = np.arange(0, len(np.unique(cluster.labels_)) + 1)
        hist, _ = np.histogram(cluster.labels_, bins=numLabels)
        hist = hist.astype("float32")
        hist /= hist.sum()
        return hist

    def _sort_hsvs(sellf, hsv_list):
        """
        Sort the list of HSV values
        :param hsv_list: List of HSV tuples
        :return: List of indexes, sorted by hue, then saturation, then value
        """
        bars_with_indexes = []
        for index, hsv_val in enumerate(hsv_list):
            bars_with_indexes.append(
                (index, hsv_val[0], hsv_val[1], hsv_val[2])
            )
        bars_with_indexes.sort(key=lambda elem: (elem[1], elem[2], elem[3]))
        return [item[0] for item in bars_with_indexes]

    def _hextriplet(self, colortuple):
        return "#" + "".join(f"{i:02X}" for i in colortuple)

    def get_dominant_color(self, image_url: str):
        req = urllib.request.urlopen(
            image_url,
            context=ssl.create_default_context(cafile=certifi.where()),
        )
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)  # 'Load it as it is'
        height, width, _ = np.shape(img)

        image = img.reshape((height * width, 3))

        num_clusters = 2
        clusters = KMeans(n_clusters=num_clusters)
        clusters.fit(image)

        # count the dominant colors and put them in "buckets"
        histogram = self._make_histogram(clusters)
        # then sort them, most-common first
        combined = zip(histogram, clusters.cluster_centers_)
        combined = sorted(combined, key=lambda x: x[0], reverse=True)

        # finally, we'll output a graphic showing the colors in order
        bars = []
        hsv_values = []
        hexs = []
        for index, rows in enumerate(combined):
            bar, rgb, hsv = self._make_bar(100, 100, rows[1])
            print(f"Bar {index + 1}")
            print(f"  RGB values: {rgb}")
            print(f"  HSV values: {hsv}")
            print(f"  Hex values: {self._hextriplet(rgb)}")
            hsv_values.append(hsv)
            bars.append(bar)
            hexs.append(self._hextriplet(rgb))
        return hexs
