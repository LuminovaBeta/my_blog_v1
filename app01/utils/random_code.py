# 依赖第三方库 PIL
# 安装命令： pip install pillow

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import string # 所有字母
import random # 随机数字

from io import BytesIO

# 随机颜色
def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def random_code(size=(184, 44), length=4, point_num=100, line_num=15):

    str_all = string.digits + string.ascii_letters
    width, height = size# 拆包

    # 生成白色背景图片对象
    img = Image.new('RGB', (width, height), color=(255, 255, 255))

    # 在这个图片上创建画布
    draw = ImageDraw.Draw(img)

    # 生成字体对象
    font = ImageFont.truetype(font='static/my/font/oborlava-v48lx.otf', size=32)

    # 书写随机文字
    valid_code = ''

    for i in range(length):
        random_char = random.choice(str_all)
        draw.text((42*i + 20, 10), random_char, (0,0,0), font=font)
        valid_code += random_char

    print(valid_code)

    # 随意生成点
    for i in range(point_num):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), random_color())

    # 随机生成线
    for i in range(line_num):
        x1 = random.randint(0, width)
        x2 = random.randint(0, width)
        y1 = random.randint(0, height)
        y2 = random.randint(0, height)
        draw.line(((x1, y1), (x2, y2)), fill=random_color(), width=2)

    # 创建一个内存句柄
    f = BytesIO()

    ## 将图片保存到内存句柄中
    img.save(f, 'PNG')

    # 读取字节数据
    data = f.getvalue()
    # print(data)

    return (data, valid_code)

if __name__ == '__main__':
    random_code()
