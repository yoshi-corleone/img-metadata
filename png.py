import struct


class Png:

    __offset = 0

    @staticmethod
    def can_parse(data):
        magic_number = struct.unpack_from("8c", data)
        return magic_number == (b'\x89', b'\x50', b'\x4E', b'\x47', b'\x0D', b'\x0A', b'\x1A', b'\x0A')

    def parse(self, png):
        self.__offset = 8

        result = {}

        while True:
            (name, length) = self.__parse_chunk(png)
            if name == "IHDR":
                (width, height, bit_depth, color_type) = struct.unpack_from(">2L2B", png, self.__offset + 8)
                result["width"] = width
                result["height"] = height
                result["mode"] = self.__get_color_mode(color_type)
                break
            self.__offset += length + 12

        return result

    def __parse_chunk(self, png):
        (length, name,) = struct.unpack_from(">L4s", png, self.__offset)
        return name.decode('utf-8'), length

    def __get_color_mode(self, color_type):
        if color_type == 0:
            return "Grayscale"
        elif color_type == 2:
            return "RGB"
        elif color_type == 3:
            return "Indexed Color"
        elif color_type == 4:
            return "Grayscale with Alpha"
        elif color_type == 6:
            return "RGB with Alpha"
        else:
            return "Unknown"


