```
project/
│── app/
│   └── main.py                   # code API FastAPI
│── tests/
│   └── test_api_contract.py      # test cơ bản cho API
│   └── api_contract.json   
│── requirements.txt              # dependencies
│── dockerfile                    # build container
│── .github/
│   └── workflows/
│       └── ci-cd.yml             # pipeline
```

```bash
python -m pip install fastapi uvicorn aiohttp netCDF4 pandas xarray zarr fsspec pytest requests jsonschema
python-multipart
```

```
http://127.0.0.1:8000/weather?lons=105.85&lats=21.03&start_year=2024&end_year=2024
```

### Thiết lập các biến bí mật (Secrets)
Bạn không bao giờ nên để thông tin nhạy cảm như SSH key hoặc mật khẩu trong mã nguồn. Thay vào đó, hãy lưu trữ chúng trong GitHub Secrets.

1. Trong kho lưu trữ GitHub của bạn, đi tới Settings -> Secrets and variables -> Actions.

2. Nhấn vào New repository secret.

3. Tạo các bí mật sau:
- SERVER_HOST: Địa chỉ IP hoặc tên miền của máy chủ.
- SERVER_USERNAME: Tên người dùng để đăng nhập vào máy chủ.
- SERVER_SSH_KEY: Khóa SSH riêng tư của bạn (đảm bảo không bao giờ chia sẻ khóa này).


```
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/1109trungpham/cicd_api.git
git push -u origin main
```