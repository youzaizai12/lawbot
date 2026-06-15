from PIL import Image

# 请将文件名替换为您的实际文件名
files = [
    "chart1_qps_20260612_171755.png",
    "chart2_response_time_20260612_171810.png",
    "chart3_success_rate_20260612_171811.png",
    "chart4_extreme_capacity_20260612_171813.png",
    "chart5_extreme_response_20260612_171814.png",
    "chart6_stability_20260612_171816.png"
]

images = [Image.open(f) for f in files]
w, h = images[0].size

# 3行2列拼接
result = Image.new('RGB', (w * 2, h * 3))
for i, img in enumerate(images):
    row, col = i // 2, i % 2
    result.paste(img, (col * w, row * h))

result.save("combined_charts.png")
print("拼接完成：combined_charts.png")