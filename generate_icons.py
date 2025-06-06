from PIL import Image
from pathlib import Path

def generate_icons():
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    resource_dir = script_dir / 'app' / 'resource'
    
    # 确保目录存在
    resource_dir.mkdir(parents=True, exist_ok=True)
    
    # 打开源图片
    img = Image.open('1.png')
    
    # 保存为 PNG
    img.save(resource_dir / 'logo.png', 'PNG')
    
    # 保存为 ICO
    # 创建多个尺寸的图标
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
    icon_images = []
    for size in sizes:
        resized_img = img.resize(size, Image.Resampling.LANCZOS)
        icon_images.append(resized_img)
    
    # 保存为 ICO，包含多个尺寸
    icon_images[0].save(
        resource_dir / 'logo.ico',
        format='ICO',
        sizes=sizes,
        append_images=icon_images[1:]
    )
    
if __name__ == '__main__':
    generate_icons() 