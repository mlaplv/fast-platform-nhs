import asyncio
from backend.utils.noise_cleaner import noise_cleaner

async def main():
    html = """
    <div>
        <h3>Thành phần nổi bật:</h3>
        <p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p>
        <p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p>
        <h3>Bảo quản</h3>
        <p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
        <p>Tránh xa tầm tay trẻ em.</p>

        <h3>Thành phần nổi bật:</h3>
        <p>Vitamin C dẫn xuất & Vitamin E: Hỗ trợ dưỡng sáng, mờ thâm, phục hồi và bảo vệ da.</p>
        <p>Chiết xuất lá hoa anh đào: Làm dịu, giảm sạm, giúp da sáng hồng.</p>
        <h3>Bảo quản</h3>
        <p>Bảo quản nơi khô ráo thoáng mát, tránh ánh nắng trực tiếp và nhiệt độ cao.</p>
        <p>Tránh xa tầm tay trẻ em.</p>
    </div>
    """
    options = {
        "stripFont": True,
        "stripAlign": True,
        "stripRedundantWrappers": True,
        "stripEmpty": True,
        "deduplicateContent": True
    }
    
    # Try aggressive mode
    cleaned = await noise_cleaner.clean(html, mode="aggressive", options=options)
    print("================ AGGRESSIVE ================")
    print(cleaned)

    # Try light mode
    cleaned2 = await noise_cleaner.clean(html, mode="light", options=options)
    print("================ LIGHT ================")
    print(cleaned2)

asyncio.run(main())
