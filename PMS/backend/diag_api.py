import asyncio
import httpx

async def diag():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Login
        login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
        print(f"Login Status: {login_res.status_code}")
        if login_res.status_code != 200:
            print(login_res.text)
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. List Tasks
        list_res = await client.get("/api/tasks", headers=headers)
        print(f"List Tasks Status: {list_res.status_code}")
        if list_res.status_code != 200:
            print(list_res.text)
            
        # 3. Create Task
        create_res = await client.post("/api/tasks", headers=headers, json={
            "title": "Diag Task",
            "task_type": "performance",
            "category": "project"
        })
        print(f"Create Task Status: {create_res.status_code}")
        if create_res.status_code != 200:
            print(create_res.text)

if __name__ == "__main__":
    asyncio.run(diag())
