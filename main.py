# นำเข้าไลบรารีที่จำเป็น
from fastapi import FastAPI, HTTPException  # สำหรับสร้าง API และจัดการ error
import requests                              # ใช้สำหรับส่ง HTTP requests
import config                                # ดึงค่าคอนฟิกต่างๆ จากไฟล์ config.py

# สร้างแอป FastAPI
app = FastAPI()

# ================================
# ฟังก์ชัน: ดึงอีเมล forwarders ทั้งหมด
# ================================
def get_all_forwarders():
    endpoint = f"{config.cpanel_host}/execute/Email/list_forwarders"  # URL ของ API
    headers = {
        "Authorization": f"cpanel {config.cpanel_user}:{config.cpanel_token}"  # เพิ่ม header auth
    }
    params = {
        "domain": config.domain  # ระบุโดเมน
    }
    response = requests.get(endpoint, headers=headers, params=params, verify=False)  # ส่ง request
    return response.json().get('data', {}).get('forwarders', [])  # คืนค่ารายการอีเมล

# ==================================
# ฟังก์ชัน: สร้างอีเมล forwarder ใหม่
# ==================================
def create_email_forwarder(local_part, forward_to):
    endpoint = f"{config.cpanel_host}/execute/Email/add_forwarder"  # endpoint สำหรับสร้าง forwarder
    headers = {
        "Authorization": f"cpanel {config.cpanel_user}:{config.cpanel_token}"  # auth header
    }
    params = {
        "domain": config.domain,           # โดเมน
        "email": local_part,               # ส่วนหน้า @ เช่น meowmail-1234
        "fwdopt": "fwd",                   # เลือกประเภทเป็น forward
        "fwdemail": forward_to             # อีเมลปลายทางที่จะส่งต่อ
    }
    response = requests.get(endpoint, headers=headers, params=params, verify=False)  # ส่งคำขอ
    return response.json()  # คืนค่าผลลัพธ์แบบ JSON

# =============================
# ฟังก์ชัน: ลบอีเมล forwarder
# =============================
def delete_email_forwarder(address):
    endpoint = f"{config.cpanel_host}/execute/Email/delete_forwarder"  # endpoint สำหรับลบ
    headers = {
        "Authorization": f"cpanel {config.cpanel_user}:{config.cpanel_token}"  # auth header
    }
    params = {
        "email": address  # ระบุอีเมลเต็มที่ต้องการลบ เช่น abc123@domain.com
    }
    response = requests.get(endpoint, headers=headers, params=params, verify=False)  # ส่ง request
    return response.json()  # คืนค่าผลลัพธ์ JSON

# =====================================
# API Endpoint: /createemail
# สร้างอีเมลแบบสุ่ม พร้อม forward ไปปลายทาง
# =====================================
@app.get("/createemail")
async def create_email():
    username = config.generate_email_username()  # สุ่มชื่ออีเมล เช่น meowmail-abc123
    result = create_email_forwarder(username, config.forward_to_email)  # ส่งไปสร้างที่ cPanel

    if result.get("status") == 1:
        # หากสำเร็จ คืนค่าชื่ออีเมลและปลายทาง
        return {
            "success": True,
            "email": f"{username}@{config.domain}",
            "forward_to": config.forward_to_email
        }
    else:
        # ถ้าล้มเหลว ส่ง error 500
        raise HTTPException(status_code=500, detail=result.get("errors", result))

# =====================================
# API Endpoint: /deleteallemail
# ลบ forwarders ทั้งหมดที่อยู่ในโดเมนที่กำหนด
# =====================================
@app.get("/deleteallemail")
async def delete_all_emails():
    try:
        forwarders = get_all_forwarders()  # ดึงรายการทั้งหมดจาก cPanel
        deleted = []  # รายการอีเมลที่ลบสำเร็จ

        for fw in forwarders:
            full_email = fw.get("address")
            if full_email.endswith(f"@{config.domain}"):  # ตรวจสอบว่าอยู่ในโดเมนเรา
                res = delete_email_forwarder(full_email)  # ลบ
                if res.get("status") == 1:
                    deleted.append(full_email)  # เพิ่มลงใน list

        # คืนค่ารายชื่ออีเมลที่ลบได้ทั้งหมด
        return {
            "success": True,
            "deleted_count": len(deleted),
            "deleted_emails": deleted
        }
    except Exception as e:
        # ถ้ามีข้อผิดพลาด ส่ง HTTP 500
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# เริ่มรันเซิร์ฟเวอร์ API
# ========================
if __name__ == "__main__":
    import uvicorn
    # รันแอปบน host 0.0.0.0 และ port ที่กำหนดจาก config
    uvicorn.run(app, host="0.0.0.0", port=config.server_port)
