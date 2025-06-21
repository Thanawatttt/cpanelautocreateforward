# Import ไลบรารีที่จำเป็น
from fastapi import FastAPI, HTTPException
from typing import List
import requests
import random
import string

# สร้างแอป FastAPI
app = FastAPI()

# === CONFIGURATION ===
# ข้อมูลการเชื่อมต่อกับ cPanel API
cpanel_user = 'user'  # ชื่อผู้ใช้ cPanel
cpanel_token = 'Api Token'  # Token API สำหรับเข้าถึง cPanel API
domain = 'Domain'  # โดเมนหลักที่ใช้จัดการ email forwarder
cpanel_host = 'URL'   # URL ของเซิร์ฟเวอร์ cPanel
forward_to_email = 'test@example.com'  # อีเมลปลายทางที่จะส่งต่อให้

# === HELPERS ===

def random_username(length=12):
    """สร้างชื่อ username สุ่มสำหรับใช้ในอีเมล"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_all_forwarders():
    """ดึงรายการ email forwarders ทั้งหมดจาก cPanel"""
    endpoint = f"{cpanel_host}/execute/Email/list_forwarders"
    headers = {
        "Authorization": f"cpanel {cpanel_user}:{cpanel_token}"
    }
    params = {
        "domain": domain
    }
    # ส่งคำขอ GET ไปยัง cPanel API
    response = requests.get(endpoint, headers=headers, params=params, verify=False)
    result = response.json()
    if result.get('status') == 1:
        # หากสำเร็จ คืนค่ารายการ forwarders
        return result.get('data', {}).get('forwarders', [])
    else:
        # หากเกิดข้อผิดพลาด โยน Exception
        raise Exception("Failed to fetch forwarders: " + str(result.get('errors', result)))

def create_email_forwarder(local_part, forward_to):
    """สร้าง email forwarder ใน cPanel โดยส่งต่อไปยังอีเมลที่กำหนด"""
    endpoint = f"{cpanel_host}/execute/Email/add_forwarder"
    headers = {
        "Authorization": f"cpanel {cpanel_user}:{cpanel_token}"
    }
    params = {
        "domain": domain,
        "email": local_part,  # ชื่อหน้า @ เช่น user@example.com -> user
        "fwdopt": "fwd",      # เลือกโหมด forward
        "fwdemail": forward_to  # อีเมลปลายทางที่จะ forward ไป
    }
    response = requests.get(endpoint, headers=headers, params=params, verify=False)
    return response.json()

def delete_email_forwarder(address):
    """ลบ email forwarder ออกจาก cPanel"""
    endpoint = f"{cpanel_host}/execute/Email/delete_forwarder"
    headers = {
        "Authorization": f"cpanel {cpanel_user}:{cpanel_token}"
    }
    params = {
        "email": address  # ที่อยู่อีเมลเต็ม (full email) ที่ต้องการลบ
    }
    response = requests.get(endpoint, headers=headers, params=params, verify=False)
    return response.json()

# === ENDPOINTS ===

@app.get("/createemail")
async def create_email():
    """สร้างอีเมลใหม่แบบสุ่ม และตั้งค่าให้ส่งต่ออีเมลไปยัง admin@meowpro.pp.ua"""
    username = random_username()  # สร้าง username สุ่ม
    result = create_email_forwarder(username, forward_to_email)

    if result.get('status') == 1:
        # หากสร้างสำเร็จ คืนค่าอีเมลและปลายทาง
        return {
            "success": True,
            "email": f"{username}@{domain}",
            "forward_to": forward_to_email
        }
    else:
        # หากสร้างไม่สำเร็จ โยนข้อผิดพลาด HTTP 500
        raise HTTPException(status_code=500, detail=result.get('errors', result))

@app.get("/deleteallemail")
async def delete_all_emails():
    """ลบ email forwarders ทั้งหมดในโดเมนที่กำหนด"""
    try:
        forwarders = get_all_forwarders()  # ดึงรายการ forwarders ทั้งหมด
        deleted = []

        for fw in forwarders:
            full_email = fw.get('address')
            if full_email.endswith(f"@{domain}"):  # กรองเฉพาะอีเมลในโดเมนนี้
                res = delete_email_forwarder(full_email)
                if res.get('status') == 1:
                    deleted.append(full_email)  # บันทึกอีเมลที่ลบได้
                else:
                    raise Exception(f"Failed to delete {full_email}: {res}")

        # คืนค่าผลลัพธ์เมื่อลบทั้งหมดแล้ว
        return {
            "success": True,
            "deleted_count": len(deleted),
            "deleted_emails": deleted
        }

    except Exception as e:
        # หากเกิดข้อผิดพลาดระหว่างกระบวนการ โยน HTTPException
        raise HTTPException(status_code=500, detail=str(e))

# === RUNNER ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)