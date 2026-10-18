================================================================
  TIEN DO VAN KIEP - GAME MO PHONG CUOC DOI TU TIEN
================================================================

1. DAY LA GI?
-------------
Mot tro choi mo phong cuoc doi tu tren trinh duyet, giong nhip
BitLife nhung trong the gioi huyen huyen phuong Dong:
- 8 dai canh gioi: Luyen Khi -> Tru Co -> Ket Dan -> Nguyen Anh
  -> Hoa Than -> Luyen Hu -> Hop The -> Dai Thua.
- Moi dai canh gioi co 12 don vi tien trien noi bo; bac 10
  (Dai Vien Man) gom 3 don vi rieng biet.
- Bien co, cau chuyen, NPC do AI sang tao qua API tuong thich
  OpenAI Chat Completions cua nha cung cap BAN chon.
- Moi thay doi du lieu deu do phan mem phia sau (backend) kiem
  soat; AI khong the tu y tang tu vi, tang tien, hoi sinh nguoi
  chet hay tao vat pham trai luat.

2. YEU CAU MAY TINH
-------------------
- Windows 10/11.
- Python 3.10 hoac moi hon (chi can cai LAN DAU).
- Internet: chi can de goi AI. Phan con lai chay hoan toan
  tren may cua ban.

3. CAI DAT (lam dung 1 lan)
---------------------------
1) Giai nen (hoac tao) thu muc TienDoVanKiep o bat ky cho nao.
2) Kiem tra da tao du cac file va thu muc theo cay o tren.
3) Nhap DOI vao start.bat. File se tu dong:
   - Kiem tra Python (bao ro cach cai neu thieu).
   - Tao moi truong Python rieng (.venv) va cai thu vien.
   - Khoi dong server, cho san sang roi moi mo trinh duyet.
   - Neu game da dang chay thi chi mo lai trinh duyen, khong
     khoi dong trung.

4. CAU HINH AI LAN DAU (QUAN TRONG)
-----------------------------------
De co bien co va cau chuyen do AI sang tao:
1) Mo game, nhan "Cai Dat AI" o thanh tren.
2) Dien 3 truong bat buoc theo tai khoan AI cua ban:
   - API Base URL: dia chi API nha cung cap cung cap.
     * Neu dia chi ket thuc bang /v1 (hoac /v2, /v3...), he
       thong tu noi /chat/completions.
     * Neu da ket thuc bang /chat/completions thi dung nguyen.
   - API Key: khoa truy cap cua ban.
   - Model ID: ten model chinh xac nha cung cap ho tro.
     KHONG duoc dien ten model ma ban khong chac chan ton tai.
3) Nhan "Kiem tra ket noi" - he thong se goi that su mot yeu
   cau va bao ket qua (thanh cong hoac nguyen nhan that bai).
4) Nhan "Luu cai dat".
Luu y: API key duoc luu trong file config/ai_config.json TREN
MAY CUA BAN, chi phan mem phia sau su dung, khong bao gio gui
cho trinh duyet hay bat ky ai khac. Khong chia se file nay.

Neu chua cau hinh AI: ban van choi duoc (tien thoi gian, tu
luyen, dot pha, nghi ngoi, tui do...) nhung se KHONG co bien
co AI. He thong se bao loi ro rang khi ban chon hanh dong can
AI chu khong gia vao thanh cong.

5. BAT DAU / LUU / TIEP TUC / DONG
----------------------------------
- Tao nhan vat: nhap ten, chon gioi tinh va than phan xuat
  than. Moi than phan co dieu kien khoi dau khac nhau.
- Choi: nhan nut "Be quan / Tien thoi gian (+X nam)" hoac chon
  hanh dong trong bang hanh dong, hoac go hanh dong tu do.
- Khi co bien co, ban PHAI chon 1 trong 3-4 phuong an; bien co
  khong tu bien mat va duoc luu lai neu ban tat trinh duyet.
- Tu dong luu: moi thay doi duoc ghi vao data/tiendovankiep.db
  ngay lap tuc. Dong trinh duyet, tat may, mo lai ngay mai -
  nhan vat van o nguyen tai. Bien co dang cho cung duoc giu.
- Nhieu nhan vat: tao nhan vat moi KHONG xoa nhan vat cu; nhan
  "Nhan vat" de quay lai danh sach va chon "Choi tiep".
- Tat game: chay stop.bat (tat server an toan). Hoac cung co
  the tat truc tiep cua so "TienDoVanKiep Server".

6. LUAT QUAN TRONG CAN BIET
---------------------------
- Tuoi tho co han; het thoi nguyen la chet that su, khong ai
  cuu duoc neu trang thai khong cho phep.
- Dot pha that bai co the lam tu vi lui, thuong trang tam ma.
- Chien dau: khong the vuot 2 tieu canh gioi de thang tran
  truc dien cong bang, du ban co la "thien tai" di nua. Am
  muu, phuc kich, dau doc... thi khac - nhung he thong van
  kiem soat hau qua.
- AI de xuat hieu ung nao cung bi gioi han va kiem tra; neu
  trai luat, he thong dieu chinh va ghi ro trong nhat ky.

7. LOI THUONG GAP
-----------------
- "Khong tim thay Python": cai Python theo huong dan trong cua
  so start.bat (nho tick Add python.exe to PATH).
- "Cai dat thu vien that bai": kiem tra mang, xoa thu muc
  .venv roi chay start.bat lai.
- "Cong 5000-5004 deu bi chiem": dong ung dung dang chiem cong
  hoac khoi dong lai may.
- AI bao 401/403: API key sai. 404: Base URL hoac Model ID
  sai. 429: het han muc/qua nhieu yeu cau. Timeout: mang yeu.
- "AI tra ve JSON khong hop le": he thong da tu thu lai 1 lan;
  neu van loi, thu model khac hoac giam temperature trong Cai
  Dat AI.
- Muon choi lai tu dau ma giu nhan vat cu: tao nhan vat moi
  trong man hinh "Nhan vat" - du lieu cu van duoc giu.

8. BAO MAT
----------
- API key chi nam trong file config/ai_config.json tren may
  ban; file .gitignore da loai no khoi kho ma nguon.
- Khong can cap quyen nao ngoai may cua ban; server chi lang
  nghe 127.0.0.1 (khong ra internet).
