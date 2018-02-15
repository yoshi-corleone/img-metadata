import struct
from exif import Exif


class Jpeg:

    __offset = 0
    __SOI = (b'\xFF', b'\xD8')
    __APP1 = (b'\xFF', b'\xE1')
    __SOS = (b'\xFF', b'\xDA')
    __EOI = (b'\xFF', b'\xD9')
    __SOFs = [
        (b'\xFF', b'\xC0'),
        (b'\xFF', b'\xC1'),
        (b'\xFF', b'\xC2'),
        (b'\xFF', b'\xC3'),
        (b'\xFF', b'\xC5'),
        (b'\xFF', b'\xC6'),
        (b'\xFF', b'\xC7'),
        (b'\xFF', b'\xC9'),
        (b'\xFF', b'\xCA'),
        (b'\xFF', b'\xCB'),
        (b'\xFF', b'\xCD'),
        (b'\xFF', b'\xCE'),
        (b'\xFF', b'\xCF'),
    ]

    @staticmethod
    def can_parse(data):
        magic_number = struct.unpack_from("2c", data)
        return magic_number == (b'\xFF', b'\xD8')

    def parse(self, jpeg):
        self.__offset = 2

        result = {}

        while True:
            segment_marker = struct.unpack_from("2c", jpeg, self.__offset)
            self.__offset += 2

            if segment_marker == self.__SOS:
                break

            if segment_marker == self.__EOI:
                break

            segment_length = struct.unpack_from(">H", jpeg, self.__offset)[0]
            for frame_header_marker in self.__SOFs:
                if segment_marker == frame_header_marker:
                    (height, width, channels) = struct.unpack_from(">HHB", jpeg, self.__offset + 3)
                    result["width"] = width
                    result["height"] = height
                    result["mode"] = self.__get_color_mode(channels)
                    break

            if segment_marker == self.__APP1:
                app1_magic = struct.unpack_from("6c", jpeg, self.__offset + 2)
                if app1_magic == (b'\x45', b'\x78', b'\x69', b'\x66', b'\x00', b'\x00'):
                    exif_parser = Exif(jpeg, self.__offset + 8, segment_length)
                    tags = [
                        (271, "maker"),
                        (272, "model"),
                        (2, "latitude"),
                        (4, "longitude"),
                        (36867, "DateTimeOriginal")
                    ]
                    for tag in tags:
                        try:
                            value = exif_parser.search_tag(jpeg, target_tag=tag[0], clear_offset=True)
                            result[tag[1]] = value
                        except ValueError:
                            pass

            self.__offset += segment_length

        return result

    def __get_color_mode(self, channels):
        if channels == 1:
            return "Grayscale"
        elif channels == 3:
            return "RGB"
        elif channels == 4:
            return "CMYK"
        else:
            return "Unknown"