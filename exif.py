import struct


class Exif:

    # デフォルトはビッグエンディアン
    __endian = ">"
    __absolute_offset = 0
    __current_offset = 0
    __length = 0

    @staticmethod
    def can_parse(data):
        magic_number = struct.unpack_from("2c", data)
        return magic_number == (b'\x49', b'\x49') or magic_number == (b'\x4D', b'\x4D')

    def __init__(self, exif, offset, length):
        self.__absolute_offset = offset
        self.__length = length

        # エンディアンを取得
        exif_endian = struct.unpack_from("2c", exif, self.__absolute_offset)
        # リトルエンディアンの場合
        if exif_endian == (b"\x49", b"\x49"):
            # リトルエンディアンを設定
            self.__endian = "<"
        # 0th IFD の先頭へ移動
        self.__current_offset = self.__absolute_offset + 8

    def search_tag(self, exif, target_tag, clear_offset):
        # ExifIFDPointer(34665) と GPSInfoIFDPointer(34853) は対象外とする
        if target_tag == 34665 or target_tag == 34853:
            raise ValueError("Pointer tag")

        # 0th IFD から検索を行う場合はオフセットのリセットが必要
        if clear_offset is True:
            self.__current_offset = self.__absolute_offset + 8

        # 現在の IFD のタグ数を取得
        (tag_count,) = struct.unpack_from("{}H".format(self.__endian), exif, self.__current_offset)
        # タグの記録位置へ移動
        self.__current_offset += 2

        # タグをループで検索
        for i in range(tag_count):
            (tag, tag_type, data_count) = struct.unpack_from("{}HHL".format(self.__endian),
                                                             exif,
                                                             self.__current_offset + (12 * i))

            # ExifIFDPointer または GPSInfoIFDPointer の場合はオフセット先に IFD があるため、再帰検索を行う
            if tag == 34665 or tag == 34853:
                # 再帰検索前のポインタ位置を一時記憶
                resume_offset = self.__current_offset
                (ifd_pointer,) = struct.unpack_from("{}L".format(self.__endian),
                                                    exif,
                                                    self.__current_offset + (12 * i) + 8)
                # ポインタ位置へ移動
                self.__current_offset = ifd_pointer + self.__absolute_offset

                try:
                    value = self.search_tag(exif, target_tag=target_tag, clear_offset=False)
                    return value
                except ValueError:
                    # ポインタが指す IFD にタグがない場合
                    # 再帰検索前のポインタ位置に戻す
                    self.__current_offset = resume_offset
                    # 元のループを再開
                    continue

            # 求めるタグと一致しなければループをスキップ
            if tag != target_tag:
                continue

            # 求めるタグの場合、値を取得して終了
            return self.__get_tag_value(exif, tag_type, data_count, self.__current_offset + (12 * i) + 8)

        # 次の IFD のオフセットを取得
        (next_ifd,) = struct.unpack_from("{}L".format(self.__endian),
                                         exif,
                                         self.__current_offset + (12 * tag_count))

        # 0 はこれ以上 IFD がないということ
        # ここまででタグが一致しなかったので、検索は失敗として例外を送出
        if next_ifd == 0:
            raise ValueError("Tag not found")

        # オフセットを更新、次の IFD に進める
        self.__current_offset = next_ifd + self.__absolute_offset
        # 再帰で IFD を検索、オフセットはリセットする必要なし
        return self.search_tag(exif, target_tag=target_tag, clear_offset=False)

    def __get_tag_value(self, exif, tag_type, data_count, offset):
        if tag_type == 1:
            data_offset = self.__get_tag_value_offset(exif, 1, data_count, offset)
            return struct.unpack_from("{}B".format(data_count), exif, data_offset)

        elif tag_type == 2:
            data_offset = self.__get_tag_value_offset(exif, 1, data_count, offset)
            (chars,) = struct.unpack_from("{}s".format(data_count - 1), exif, data_offset)
            return chars.decode('utf-8')

        elif tag_type == 3:
            data_offset = self.__get_tag_value_offset(exif, 2, data_count, offset)
            return struct.unpack_from("{0}{1}H".format(self.__endian, data_count), exif, data_offset)

        elif tag_type == 4:
            data_offset = self.__get_tag_value_offset(exif, 4, data_count, offset)
            return struct.unpack_from("{0}{1}L".format(self.__endian, data_count), exif, data_offset)

        elif tag_type == 5:
            data_offset = self.__get_tag_value_offset(exif, 8, data_count, offset)
            return struct.unpack_from("{0}{1}L".format(self.__endian, data_count * 2), exif, data_offset)

        elif tag_type == 6:
            data_offset = self.__get_tag_value_offset(exif, 1, data_count, offset)
            return struct.unpack_from("{}b".format(data_count), exif, data_offset)

        elif tag_type == 7:
            data_offset = self.__get_tag_value_offset(exif, 1, data_count, offset)
            (byte_array,) = struct.unpack_from("{}b".format(data_count), exif, data_offset)
            return byte_array

        elif tag_type == 8:
            data_offset = self.__get_tag_value_offset(exif, 2, data_count, offset)
            return struct.unpack_from("{0}{1}h".format(self.__endian, data_count), exif, data_offset)

        elif tag_type == 9:
            data_offset = self.__get_tag_value_offset(exif, 4, data_count, offset)
            return struct.unpack_from("{0}{1}l".format(self.__endian, data_count), exif, data_offset)

        elif tag_type == 10:
            data_offset = self.__get_tag_value_offset(exif, 8, data_count, offset)
            return struct.unpack_from("{0}{1}l".format(self.__endian, data_count * 2), exif, data_offset)

        elif tag_type == 11:
            data_offset = self.__get_tag_value_offset(exif, 4, data_count, offset)
            return struct.unpack_from("{0}{1}f".format(self.__endian, data_count), exif, data_offset)

        elif tag_type == 12:
            data_offset = self.__get_tag_value_offset(exif, 8, data_count, offset)
            return struct.unpack_from("{0}{1}d".format(self.__endian, data_count), exif, data_offset)

    def __get_tag_value_offset(self, exif, data_size, data_count, offset):
        # データ型のサイズとデータ個数を掛けたサイズが 4 バイト以上であればポインタ
        if data_size * data_count > 4:
            # ポインタの指すオフセットを返す
            (value_offset,) = struct.unpack_from("{}L".format(self.__endian), exif, offset)
            return self.__absolute_offset + value_offset

        # 通常のデータ領域のオフセットを返す
        return offset
