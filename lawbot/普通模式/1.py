from PIL import Image
import os

# 图片文件列表（按顺序）
image_files = [
    "chart1_qps_20260612_191200.png",
    "chart2_response_time_20260612_191204.png",
    "chart3_success_rate_20260612_191206.png",
    "chart4_extreme_capacity_20260612_191208.png",
    "chart5_extreme_response_20260612_191210.png",
    "chart6_stability_20260612_191212.png"
]

# 读取图片
images = [Image.open(f) for f in image_files]

# 假设每张图片尺寸相同，获取宽度和高度
width, height = images[0].size

# 创建3行×2列的大图
rows, cols = 3, 2
result = Image.new('RGB', (width * cols, height * rows))

# 拼接
for i, img in enumerate(images):
    row = i // cols
    col = i % cols
    result.paste(img, (col * width, row * height))

# 保存
result.save("combined_charts.png")
print("拼接完成：combined_charts.png")