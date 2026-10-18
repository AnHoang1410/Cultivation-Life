# -*- coding: utf-8 -*-
"""Game engine: luat choi, tu vi, thoi gian, chien dau, vat pham, NPC, the luc, nhat ky.

Engine la nguon du lieu dang tin cay duy nhat:
- AI chi de xuat hieu ung; moi hieu ung deu duoc kiem tra va gioi han truoc khi ghi vao CSDL.
- Quy tac vuot cap khieu chien duoc thuc thi bang code trong _combat_verdict.
- Tien trien tu vi dung 12 don vi noi bo moi dai canh gioi (Dai Vien Man = 3 don vi).
"""
import json
import random

import database as db
import ai_service as aisvc


class GameError(Exception):
    """Loi luat choi, thong bao truc tiep cho nguoi choi."""


# ==================== CAU HINH COT LOI ====================
REALMS = ["Luyện Khí", "Trúc Cơ", "Kết Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Hợp Thể", "Đại Thừa"]
STAGES = ["Sơ Kỳ", "Trung Kỳ", "Hậu Kỳ", "Đại Viên Mãn"]
TIME_STEP_YEARS = [1, 2, 3, 5, 8, 12, 18, 25]          # so nam moi lan bam theo dai canh gioi
REALM_LIFESPAN_BONUS = [20, 50, 120, 240, 400, 650, 1000, 1600]  # thoi them theo canh gioi
MAX_PROGRESS = 12.0                                     # 12 don vi noi bo = 1 dai canh gioi

STATUS_LIST = ["trọng thương", "trung độc", "tâm ma", "kiệt sức", "bị truy sát"]
ITEM_TYPES = ["đan dược", "pháp bảo", "linh thảo", "nguyên liệu", "công pháp giản", "tạp vật"]
REL_LABELS = {"kẻ thù": -70, "đối địch": -35, "xa lạ": 5, "quen biết": 12, "bạn bè": 32,
              "đồng minh": 45, "thân thiết": 58, "tri kỷ": 80}

PILL_EFFECTS = {
    "Hồi Khí Đan": {"health": 10},
    "Liệu Thương Đan": {"health": 25},
    "Tụ Linh Đan": {"progress": 2.0},
    "Giải Độc Đan": {"remove_status": "trung độc"},
    "Tĩnh Tâm Đan": {"remove_status": "tâm ma", "mind": 5},
    "Trường Sinh Đan": {"lifespan": 20},
    "Trúc Cơ Đan": {"breakthrough_bonus": 0.15},   # tu dong dung khi dot pha
    "Đột Phá Đan": {"breakthrough_bonus": 0.25},   # tu dong dung khi dot pha
}
DIRECT_USE_PILLS = ["Hồi Khí Đan", "Liệu Thương Đan", "Tụ Linh Đan",
                    "Giải Độc Đan", "Tĩnh Tâm Đan", "Trường Sinh Đan"]

ROOTS = [
    {"key": "thien", "name": "Thiên Linh Căn", "mult": 2.0, "weight": 1,
     "desc": "Linh căn vạn dặm mới một, hấp thu linh khí nhanh gấp bội"},
    {"key": "kim", "name": "Kim Linh Căn", "mult": 1.5, "weight": 2, "desc": "Đơn hành kim, cực hợp luyện khí"},
    {"key": "moc", "name": "Mộc Linh Căn", "mult": 1.5, "weight": 2, "desc": "Đơn hành mộc, cực hợp đan đạo"},
    {"key": "thuy", "name": "Thủy Linh Căn", "mult": 1.5, "weight": 2, "desc": "Đơn hành thủy, thần thức thuần hậu"},
    {"key": "hoa", "name": "Hỏa Linh Căn", "mult": 1.5, "weight": 2, "desc": "Đơn hành hỏa, dược hỏa tự sinh"},
    {"key": "tho", "name": "Thổ Linh Căn", "mult": 1.5, "weight": 2, "desc": "Đơn hành thổ, căn cốt vững chắc"},
    {"key": "song_km", "name": "Kim Mộc Song Linh Căn", "mult": 1.2, "weight": 6, "desc": "Song hành, khá cân bằng"},
    {"key": "song_th", "name": "Thủy Hỏa Song Linh Căn", "mult": 1.2, "weight": 6, "desc": "Song hành, thủy hỏa tương tế"},
    {"key": "tam", "name": "Tam Linh Căn", "mult": 1.0, "weight": 10, "desc": "Tam hành hỗn tạp, tốc độ trung bình"},
    {"key": "tap", "name": "Tạp Linh Căn", "mult": 0.8, "weight": 14, "desc": "Ngũ hành tạp, tu luyện chậm"},
    {"key": "phe", "name": "Phế Linh Căn", "mult": 0.6, "weight": 8, "desc": "Linh căn gần tắc nghẽn, con đường gian nan"},
]

ORIGINS = {
    "nguoi_pham": {"label": "Người Phàm",
                   "desc": "Con nhà nông dân, chưa từng chạm vào tu đạo. Nghèo khó nhưng tự do.",
                   "stones": (10, 40), "reputation": 0, "technique": ("Vô Danh Khẩu Quyết", 1),
                   "age": 16, "base_life": 80, "apt_bonus": 0, "realm": 0, "progress": 1.0},
    "mo_coi": {"label": "Trẻ Mồ Côi",
               "desc": "Cha mẹ mất sớm, lớn lên trong giang hồ loạn thế. Ít tiền nhưng lì lợm.",
               "stones": (0, 15), "reputation": 0, "technique": ("Vô Danh Khẩu Quyết", 1),
               "age": 15, "base_life": 78, "apt_bonus": 5, "realm": 0, "progress": 1.0},
    "the_gia": {"label": "Con Cháu Tu Tiên Thế Gia",
                "desc": "Sinh ra trong thế gia tu tiên, có người che chở, công pháp tốt, tiền rủng rỉnh.",
                "stones": (300, 600), "reputation": 10, "technique": ("Huyền Dương Công", 3),
                "age": 16, "base_life": 90, "apt_bonus": 10, "realm": 0, "progress": 2.0},
    "ngoai_mon": {"label": "Đệ Tử Ngoại Môn",
                  "desc": "Vừa qua khảo hạch, trở thành đệ tử ngoại môn Thanh Vân Tông. Có chỗ dựa nhưng cũng có ràng buộc.",
                  "stones": (50, 120), "reputation": 5, "technique": ("Thanh Vân Quyết", 2),
                  "age": 16, "base_life": 85, "apt_bonus": 5, "realm": 0, "progress": 2.0,
                  "auto_faction": "Thanh Vân Tông"},
    "suy_tan": {"label": "Hậu Duệ Thế Lực Suy Tàn",
                "desc": "Gia tộc bị hủy diệt, ngươi là giọt máu cuối cùng, mang mối thù và chút gia sản giấu được.",
                "stones": (100, 250), "reputation": 3, "technique": ("Ngũ Hành Quyết", 2),
                "age": 18, "base_life": 82, "apt_bonus": 5, "realm": 0, "progress": 1.5},
}

ORIGIN_ITEMS = {
    "the_gia": [("Liệu Thương Đan", "đan dược", 2, 2, "Đan cầm máu, hồi phục 25 sức khỏe.")],
    "ngoai_mon": [("Hồi Khí Đan", "đan dược", 2, 3, "Hồi phục 10 sức khỏe.")],
    "suy_tan": [("Tụ Linh Đan", "đan dược", 3, 1, "Tăng thêm 2 đơn vị tu vi.")],
    "mo_coi": [("Hồi Khí Đan", "đan dược", 1, 1, "Hồi phục 10 sức khỏe.")],
}

STARTER_FACTIONS = [
    {"name": "Thanh Vân Tông", "type": "Tông môn tu tiên", "leader": "Huyền Tâm Chân Nhân",
     "resources": "Đan dược, công pháp, linh điền", "reputation": 60, "power_realm": 5,
     "territory": "Thanh Vân sơn mạch",
     "description": "Tông môn chính đạo lớn nhất vùng, coi trọng căn cơ và kỷ luật."},
    {"name": "Bách Thảo Đường", "type": "Tổ chức đan đạo", "leader": "Dược Lão",
     "resources": "Linh thảo quý, lò đan cổ", "reputation": 45, "power_realm": 4,
     "territory": "Bách Thảo cốc", "description": "Thánh địa luyện đan, đan dược bán ra khắp vùng."},
    {"name": "Vạn Bảo Các", "type": "Thương hội", "leader": "Kim Vạn Bảo",
     "resources": "Tuyến thương mại, pháp bảo các loại", "reputation": 30, "power_realm": 3,
     "territory": "Phường thị Vạn Bảo",
     "description": "Thương hội giàu có, trả đủ linh thạch là mua được gần như mọi thứ."},
    {"name": "Huyết Ảnh Lâu", "type": "Tổ chức sát thủ", "leader": "Ảnh Chủ",
     "resources": "Tình báo, độc dược", "reputation": -40, "power_realm": 4, "territory": "Không rõ",
     "description": "Tổ chức ám sát thần bí, nhận nhiệm vụ không hỏi đạo đức."},
    {"name": "Thiết Ưng Hội", "type": "Thế lực săn yêu", "leader": "Thiết Ưng",
     "resources": "Yêu thú vật liệu", "reputation": 20, "power_realm": 3,
     "territory": "Biên giới Hoang Nguyên",
     "description": "Tập hợp thợ săn yêu thú, hung hãn và thực dụng."},
    {"name": "Tán Tu Liên Minh", "type": "Liên minh tán tu", "leader": "Cô Vân Tán Nhân",
     "resources": "Mạng lưới tán tu, tin tức", "reputation": 15, "power_realm": 3,
     "territory": "Thị trấn biên giới",
     "description": "Liên minh lỏng lẻo của những tán tu không muốn bị ràng buộc."},
    {"name": "Hỏa Vân Thế Gia", "type": "Tu tiên thế gia", "leader": "Hỏa Vân Lão Tổ",
     "resources": "Linh mạch, thế lực chính trị", "reputation": 35, "power_realm": 4,
     "territory": "Hỏa Vân thành", "description": "Thế gia cậy thế lâu đời, trọng huyết thống và lợi ích."},
]

ACTIONS = {
    # --- Tu luyện ---
    "cultivate": {"label": "Tu luyện thông thường (+1 năm)", "category": "tu_luyen", "kind": "time",
                  "mode": "cultivate", "hint": "Một năm tu luyện bình thường tại nơi ở hiện tại."},
    "seclude": {"label": "Bế quan dài hạn", "category": "tu_luyen", "kind": "time",
                "mode": "seclude", "hint": "Bế quan một khoảng dài năm, tu luyện nhanh hơn nhưng ít tiếp xúc bên ngoài."},
    "breakthrough": {"label": "Thử đột phá", "category": "tu_luyen", "kind": "engine",
                     "hint": "Chỉ khi tu vi đạt Đại Viên Mãn trọn vẹn (tiến độ nội bộ 3/3)."},
    "research_technique": {"label": "Nghiên cứu công pháp", "category": "tu_luyen", "kind": "ai",
                           "hint": "Tìm hiểu, nâng cấp hoặc tìm kiếm công pháp tu luyện mới."},
    "find_leystream": {"label": "Tìm nơi linh khí tốt", "category": "tu_luyen", "kind": "ai",
                       "hint": "Đi tìm động phủ, linh mạch hoặc nơi linh khí nồng đậm để tu luyện."},
    "calm_mind": {"label": "Khắc phục tâm ma / thương thế", "category": "tu_luyen", "kind": "engine",
                  "hint": "Tĩnh tọa hóa giải tâm ma hoặc dưỡng thương."},
    # --- Bí cảnh ---
    "find_secret_realm": {"label": "Tìm kiếm bí cảnh", "category": "bi_canh", "kind": "ai",
                           "hint": "Truy tìm tin đồn về bí cảnh vừa xuất hiện."},
    "explore_location": {"label": "Khám phá địa điểm", "category": "bi_canh", "kind": "ai",
                         "hint": "Khám phá một địa điểm cụ thể trong vùng."},
    "hunt_beasts": {"label": "Săn yêu thú", "category": "bi_canh", "kind": "ai",
                    "hint": "Săn yêu thú lấy vật liệu và rèn chiến đấu."},
    "seek_herbs": {"label": "Truy tìm linh dược", "category": "bi_canh", "kind": "ai",
                   "hint": "Tìm linh dược trong núi sâu."},
    "investigate_ruins": {"label": "Điều tra di tích", "category": "bi_canh", "kind": "ai",
                          "hint": "Điều tra di tích hoặc động phủ bỏ hoang."},
    "explore_cave": {"label": "Thám hiểm động phủ", "category": "bi_canh", "kind": "ai",
                     "hint": "Mạo hiểm vào một động phủ chưa biết."},
    "escape_danger": {"label": "Đào thoát khi hiểm nguy", "category": "bi_canh", "kind": "ai",
                      "hint": "Chuẩn bị và thực hiện kế hoạch thoát hiểm."},
    # --- Nghề nghiệp ---
    "refine_pill": {"label": "Luyện đan", "category": "nghe_nghiep", "kind": "ai",
                    "hint": "Dùng lò đan chế tạo đan dược (linh căn hợp đan đạo sẽ có lợi thế)."},
    "refine_artifact": {"label": "Luyện khí", "category": "nghe_nghiep", "kind": "ai",
                        "hint": "Rèn luyện pháp bảo từ nguyên liệu."},
    "gather_materials": {"label": "Thu thập nguyên liệu", "category": "nghe_nghiep", "kind": "ai",
                         "hint": "Đi thu thập linh thảo, quáng thạch, yêu vật."},
    "learn_recipe": {"label": "Học công thức", "category": "nghe_nghiep", "kind": "ai",
                     "hint": "Học công thức đan mới hoặc đồ phổ mới."},
    "take_order": {"label": "Nhận đơn hàng", "category": "nghe_nghiep", "kind": "ai",
                   "hint": "Nhận đơn chế tạo hoặc nhiệm vụ thuê."},
    "trade_goods": {"label": "Trao đổi / bán vật phẩm", "category": "nghe_nghiep", "kind": "ai",
                    "hint": "Mang vật phẩm trong túi đi trao đổi hoặc bán."},
    "develop_career": {"label": "Phát triển nghề nghiệp", "category": "nghe_nghiep", "kind": "ai",
                       "hint": "Phát triển con đường nghề nghiệp theo thế mạnh của ngươi."},
    # --- Thế lực ---
    "learn_about_sect": {"label": "Tìm hiểu tông môn", "category": "the_luc", "kind": "ai",
                         "hint": "Thu thập thông tin về các tông môn, thế lực trong vùng."},
    "request_join": {"label": "Xin gia nhập tông môn", "category": "the_luc", "kind": "ai",
                     "requires": "no_faction", "hint": "Xin gia nhập một tông môn tu tiên."},
    "join_other": {"label": "Gia nhập thế lực khác", "category": "the_luc", "kind": "ai",
                   "requires": "no_faction", "hint": "Gia nhập thương hội, liên minh, tổ chức..."},
    "leave_faction": {"label": "Rời khỏi thế lực", "category": "the_luc", "kind": "ai",
                      "requires": "has_faction", "hint": "Rời khỏi thế lực hiện tại."},
    "found_faction": {"label": "Thành lập thế lực (500 linh thạch)", "category": "the_luc", "kind": "ai",
                      "requires": "found_resources",
                      "hint": "Thành lập thế lực riêng, cần 500 linh thạch và danh tiếng từ 20 trở lên."},
    "recruit_members": {"label": "Tuyển mộ thành viên", "category": "the_luc", "kind": "ai",
                        "hint": "Chiêu mộ người theo ngươi hoặc cho thế lực của ngươi."},
    "assign_task": {"label": "Giao nhiệm vụ cho thuộc hạ", "category": "the_luc", "kind": "ai",
                    "hint": "Sai khiến thuộc hạ hoặc đồng đội làm việc."},
    "build_reputation": {"label": "Xây dựng danh tiếng", "category": "the_luc", "kind": "ai",
                         "hint": "Tạo tiếng tăm trong giới tu tiên."},
    "contest_power": {"label": "Tranh chấp tài nguyên / quyền lực", "category": "the_luc", "kind": "ai",
                      "hint": "Tranh đoạt mỏ linh thạch, địa bàn hoặc địa vị."},
    # --- Xã giao ---
    "make_friend": {"label": "Kết bạn", "category": "xa_giao", "kind": "ai",
                    "hint": "Chủ động kết giao với người mới."},
    "bond_npc": {"label": "Kết giao với người quen", "category": "xa_giao", "kind": "ai",
                 "requires": "has_npc", "hint": "Làm sâu sắc quan hệ với người ngươi đã quen."},
    "seek_master": {"label": "Tìm kiếm sư phụ", "category": "xa_giao", "kind": "ai",
                    "hint": "Tìm bậc tiền bối nhận ngươi làm đệ tử hoặc chỉ điểm."},
    "take_apprentice": {"label": "Nhận đệ tử", "category": "xa_giao", "kind": "ai",
                        "requires": "realm_ket_dan", "hint": "Nhận người theo ngươi tu luyện."},
    "cooperate": {"label": "Hợp tác", "category": "xa_giao", "kind": "ai",
                  "hint": "Đề xuất hợp tác trong một kế hoạch cụ thể."},
    "negotiate": {"label": "Thương lượng", "category": "xa_giao", "kind": "ai",
                  "hint": "Đàm phán một thỏa thuận."},
    "romance": {"label": "Tình cảm", "category": "xa_giao", "kind": "ai",
                "hint": "Tìm kiếm hoặc duy trì quan hệ tình cảm."},
    "make_enemy": {"label": "Gây thù", "category": "xa_giao", "kind": "ai",
                   "hint": "Chủ động gây thù với ai đó."},
    "revenge": {"label": "Trả thù", "category": "xa_giao", "kind": "ai",
                "requires": "has_enemy", "hint": "Trả thù kẻ có thâm thù với ngươi."},
    "reconcile": {"label": "Hòa giải", "category": "xa_giao", "kind": "ai",
                  "requires": "has_npc", "hint": "Hòa giải một mối quan hệ căng thẳng."},
    # --- Kinh tế ---
    "buy_sell": {"label": "Mua bán tại phường thị", "category": "kinh_te", "kind": "ai",
                 "hint": "Đến phường thị mua bán."},
    "manage_assets": {"label": "Quản lý tài sản", "category": "kinh_te", "kind": "ai",
                      "hint": "Đầu tư, sinh lời từ tài sản."},
    "hire_help": {"label": "Thuê người làm", "category": "kinh_te", "kind": "ai",
                  "hint": "Thuê hộ vệ hoặc người làm việc."},
    "take_quest": {"label": "Nhận nhiệm vụ", "category": "kinh_te", "kind": "ai",
                   "hint": "Nhận nhiệm vụ từ bảng nhiệm vụ."},
    "rest": {"label": "Nghỉ ngơi và dưỡng thương", "category": "kinh_te", "kind": "engine",
             "hint": "Nghỉ ngơi hồi phục sức khỏe và tâm cảnh."},
    "find_home": {"label": "Tìm nơi cư trú", "category": "kinh_te", "kind": "ai",
                  "hint": "Tìm động phủ hoặc nơi ở riêng."},
    "manage_resources": {"label": "Quản lý tài nguyên", "category": "kinh_te", "kind": "ai",
                         "hint": "Sắp xếp, phân bổ tài nguyên đang có."},
}

QUIET_YEAR_LINES = [
    "Một năm tu luyện trôi qua êm ả, linh lực trong đan điền thêm thuần hậu.",
    "Năm nay ngươi chuyên tâm điều tức, căn cơ thêm vững.",
    "Một năm bình lặng: ăn ngủ điều độ, tu vi tiến triển đều đặn.",
    "Bốn mùa luân chuyển, ngươi dành phần lớn thời gian ngồi thiền luyện khí.",
    "Năm trôi qua không sóng gió, thần thức của ngươi sắc bén hơn chút ít.",
    "Một năm cần mẫn, linh khí theo hơi thở tích lũy ngày càng dày.",
]

FLAVOR_LINES = [
    "Giữa năm có đám mây linh khí dị thường bay qua vùng ngươi ở.",
    "Ngươi nghe tin vài tán tu gần đó tranh đoạt linh thảo mà động thủ.",
    "Một phường thị nhỏ mở cửa vài ngày rồi lại đóng.",
    "Tin đồn về một bí cảnh nào đó lan khắp vùng, chưa ai kiểm chứng.",
    "Gió núi mang theo tiếng thú rống xa xa.",
    "Ngươi nhặt được vài mảnh linh thạch vụn trên đường tu luyện, coi như điềm nhỏ.",
]

THEMES = [
    "một bí cảnh mới xuất hiện", "thị phi trong tông môn", "một thương đoàn cần người hộ tống",
    "dị tượng thiên địa gần đây", "mối ân oán giang hồ cũ được nhắc lại", "một phiên chợ phường thị sắp mở",
    "một tán tu bị thương cầu cứu", "yêu thú xuất hiện gần khu tu sĩ sinh sống",
    "một cuộc tỷ thí luận kiếm", "tin tức về linh dược hiếm", "một nhóm tu sĩ lạ mặt đến vùng này",
    "thất lạc cổ vật trong đền cũ",
]


# ==================== TIEN ICH ====================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def weighted_choice(items):
    total = sum(i["weight"] for i in items)
    r = random.uniform(0, total)
    acc = 0.0
    for i in items:
        acc += i["weight"]
        if r <= acc:
            return i
    return items[-1]


def match_pill(name):
    n = (name or "").lower()
    for key in DIRECT_USE_PILLS:
        if key.lower() in n:
            return key
    return None


def rel_label(v):
    if v <= -60:
        return "kẻ thù"
    if v <= -20:
        return "đối địch"
    if v < 10:
        return "xa lạ"
    if v < 30:
        return "quen biết"
    if v < 55:
        return "bạn bè"
    if v < 80:
        return "thân thiết"
    return "tri kỷ"


def get_character(conn, char_id):
    row = db.query_one(conn, "SELECT * FROM characters WHERE id=?", (char_id,))
    if not row:
        raise GameError("Không tìm thấy nhân vật.")
    row["statuses"] = json.loads(row.get("statuses") or "[]")
    row["alive"] = bool(row["alive"])
    return row


def add_log(conn, char_id, age, etype, content):
    conn.execute(
        "INSERT INTO log_entries (character_id, age, event_type, content, created_at) VALUES (?,?,?,?,?)",
        (char_id, int(age), etype, content, db.now_str()))


def total_lifespan(char):
    return int(char["base_lifespan"]) + REALM_LIFESPAN_BONUS[char["realm_index"]] + int(char["extra_lifespan"])


def tier_of(realm_index, progress):
    """Tier = dai canh gioi * 4 + tieu canh gioi (0..3). Quy tac vuot cap dua tren tier."""
    bac = max(1, min(10, int(progress)))
    return realm_index * 4 + min(3, (bac - 1) // 3)


def cultivation_view(char):
    ri = char["realm_index"]
    p = float(char["progress"])
    bac = max(1, min(10, int(p)))
    stage = STAGES[min(3, (bac - 1) // 3)]
    dvm = None
    full = REALMS[ri] + " — Bậc " + str(bac) + " — " + stage
    if bac == 10:
        internal = min(3.0, p - 9.0)
        dvm = {"current": max(1, int(internal)), "max": 3, "fraction": internal / 3.0}
        full = (REALMS[ri] + " — Bậc 10 — Đại Viên Mãn | Tiến độ nội bộ "
                + str(dvm["current"]) + "/3")
    return {
        "realm_index": ri, "realm_name": REALMS[ri], "level": bac, "stage": stage,
        "full": full, "progress": round(p, 2), "max_progress": 12,
        "progress_fraction": p / 12.0, "dvm": dvm,
        "can_breakthrough": p >= MAX_PROGRESS,
        "at_cap": ri >= 7 and p >= MAX_PROGRESS,
    }


def public_char(c):
    return {
        "id": c["id"], "name": c["name"], "gender": c["gender"],
        "origin_key": c["origin_key"], "origin_label": c["origin_label"],
        "root_name": c["root_name"], "root_mult": c["root_mult"],
        "aptitude": c["aptitude"], "comprehension": c["comprehension"], "bone": c["bone"],
        "luck": c["luck"], "charm": c["charm"], "spirit_sense": c["spirit_sense"],
        "health": round(float(c["health"]), 1), "mind": round(float(c["mind"]), 1),
        "reputation": round(float(c["reputation"]), 1),
        "technique_name": c["technique_name"], "technique_quality": c["technique_quality"],
        "spirit_stones": c["spirit_stones"], "age": c["age"],
        "statuses": c["statuses"], "alive": bool(c["alive"]),
    }


def npc_public(n):
    return {
        "id": n["id"], "name": n["name"], "identity": n["identity"],
        "realm_index": n["realm_index"], "realm_name": REALMS[n["realm_index"]],
        "personality": n["personality"], "goal": n["goal"],
        "relationship_value": round(float(n["relationship_value"]), 1),
        "relationship_label": rel_label(n["relationship_value"]),
        "role": n["role"], "alive": bool(n["alive"]),
    }


# ==================== TAO NHAN VAT ====================
def build_origin_npcs(origin_key):
    if origin_key == "the_gia":
        return [
            {"name": "Lâm Chấn Sơn", "identity": "Gia chủ thế gia, phụ thân ngươi", "realm_index": 3,
             "progress": 6, "personality": "Nghiêm khắc, trọng gia tộc", "goal": "Đưa gia tộc lên đỉnh",
             "rel": 55, "role": "phụ thân"},
            {"name": "Lâm Tú Nhi", "identity": "Muội muội đồng phụ", "realm_index": 0, "progress": 3,
             "personality": "Linh hoạt, tò mò", "goal": "Vượt qua huynh trưởng", "rel": 45, "role": "muội muội"},
            {"name": "Cố Vân Kiếm", "identity": "Thiên tử kiêu tử của thế gia đối đầu", "realm_index": 1,
             "progress": 8, "personality": "Kiêu ngạo, thích tranh đấu",
             "goal": "Đè bẹp mọi thiên tài cùng thế hệ", "rel": -40, "role": "đối thủ"},
        ]
    if origin_key == "ngoai_mon":
        return [
            {"name": "Tô Nhược Hàn", "identity": "Sư huynh dẫn dắt ngươi ở ngoại môn", "realm_index": 1,
             "progress": 6, "personality": "Trầm ổn, thích giúp đỡ", "goal": "Vào nội môn",
             "rel": 40, "role": "sư huynh"},
            {"name": "Triệu Cương", "identity": "Đệ tử ngoại môn hay gây sự", "realm_index": 0,
             "progress": 4, "personality": "Gàn bướng, nhỏ mọn", "goal": "Lấn át người khác",
             "rel": -25, "role": "đồng môn"},
        ]
    if origin_key == "suy_tan":
        return [
            {"name": "Trần Trung", "identity": "Lão quản gia trung thành của gia tộc cũ", "realm_index": 1,
             "progress": 3, "personality": "Trung nghĩa, cẩn trọng", "goal": "Bảo vệ hậu duệ chủ gia",
             "rel": 60, "role": "lão quản gia"},
            {"name": "Huyết Lang Tử", "identity": "Tu sĩ bí ẩn từng tham gia hủy diệt thế lực ngươi",
             "realm_index": 2, "progress": 7, "personality": "Tàn nhẫn, ưa sát lục",
             "goal": "Xóa sạch dấu vết quá khứ", "rel": -80, "role": "kẻ thù giết gia tộc"},
        ]
    if origin_key == "mo_coi":
        return [
            {"name": "Thạch Đầu", "identity": "Huynh đệ kết nghĩa từ thuở nhỏ", "realm_index": 0,
             "progress": 1, "personality": "Chất phác, nghĩa khí", "goal": "Sống sót qua từng ngày",
             "rel": 50, "role": "huynh đệ kết nghĩa"},
            {"name": "Lão Khất", "identity": "Lão ăn mày bí ẩn hay ngồi trước chợ", "realm_index": 1,
             "progress": 5, "personality": "Điên điên đại đại", "goal": "Không ai biết",
             "rel": 15, "role": "nhân vật bí ẩn"},
        ]
    return [
        {"name": "Lão Trương", "identity": "Người gác đê của thôn, từng là tán tu", "realm_index": 0,
         "progress": 5, "personality": "Trầm lặng, bí ẩn", "goal": "Ẩn dật qua đời",
         "rel": 20, "role": "láng giềng"},
        {"name": "Thôn Trưởng", "identity": "Thôn trưởng quê ngươi", "realm_index": 0, "progress": 1,
         "personality": "Thực dụng", "goal": "Giữ thôn yên bình", "rel": 10, "role": "thôn trưởng"},
    ]


def create_character(conn, payload):
    name = str(payload.get("name", "")).strip()
    if not (1 <= len(name) <= 40):
        raise GameError("Tên nhân vật cần từ 1 đến 40 ký tự.")
    gender = payload.get("gender") or random.choice(["Nam", "Nữ"])
    if gender not in ("Nam", "Nữ", "Khác"):
        gender = random.choice(["Nam", "Nữ"])
    origin_key = payload.get("origin_key") or random.choice(list(ORIGINS.keys()))
    if origin_key not in ORIGINS:
        raise GameError("Thân phận xuất thân không hợp lệ.")
    origin = ORIGINS[origin_key]
    root = weighted_choice(ROOTS)
    aptitude = int(clamp(random.randint(15, 90) + origin["apt_bonus"], 1, 100))
    comprehension = random.randint(15, 95)
    bone = random.randint(15, 95)
    luck = random.randint(5, 95)
    charm = random.randint(10, 95)
    mind = random.randint(55, 90)
    age = origin["age"]
    base_life = origin["base_life"] + bone // 5
    tech_name, tech_q = origin["technique"]
    stones = random.randint(*origin["stones"])
    now = db.now_str()
    cur = conn.execute(
        """INSERT INTO characters
           (name, gender, origin_key, origin_label, root_key, root_name, root_mult,
            aptitude, comprehension, bone, luck, charm, spirit_sense, health, mind,
            reputation, technique_name, technique_quality, spirit_stones, age,
            base_lifespan, realm_index, progress, statuses, alive, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (name, gender, origin_key, origin["label"], root["key"], root["name"], root["mult"],
         aptitude, comprehension, bone, luck, charm, 10 + comprehension // 10, 100.0, float(mind),
         float(origin["reputation"]), tech_name, tech_q, stones, age,
         base_life, origin["realm"], origin["progress"], "[]", 1, now, now))
    char_id = cur.lastrowid

    for fac in STARTER_FACTIONS:
        conn.execute(
            """INSERT INTO factions (character_id, name, type, leader, resources, reputation,
               power_realm, territory, description, is_player_founded)
               VALUES (?,?,?,?,?,?,?,?,?,0)""",
            (char_id, fac["name"], fac["type"], fac["leader"], fac["resources"],
             fac["reputation"], fac["power_realm"], fac["territory"], fac["description"]))

    faction_id = None
    if origin.get("auto_faction"):
        row = db.query_one(conn, "SELECT id FROM factions WHERE character_id=? AND name=?",
                           (char_id, origin["auto_faction"]))
        if row:
            faction_id = row["id"]
            conn.execute("UPDATE characters SET faction_id=? WHERE id=?", (faction_id, char_id))

    for npc in build_origin_npcs(origin_key):
        conn.execute(
            """INSERT INTO npcs (character_id, name, identity, realm_index, progress, personality,
               goal, relationship_value, role, alive, created_age)
               VALUES (?,?,?,?,?,?,?,?,?,1,?)""",
            (char_id, npc["name"], npc["identity"], npc["realm_index"], npc["progress"],
             npc["personality"], npc["goal"], npc["rel"], npc["role"], age))

    for (iname, itype, iq, iqty, idesc) in ORIGIN_ITEMS.get(origin_key, []):
        conn.execute(
            """INSERT INTO inventory (character_id, name, item_type, quality, quantity,
               description, usable_key, equipped) VALUES (?,?,?,?,?,?,?,0)""",
            (char_id, iname, itype, iq, iqty, idesc, match_pill(iname)))

    add_log(conn, char_id, age, "he_thong",
            "Ngươi sinh ra làm " + origin["label"] + ", linh căn: " + root["name"] + ".")
    add_log(conn, char_id, age, "he_thong",
            "Bắt đầu con đường tu tiên với công pháp " + tech_name + " (phẩm " + str(tech_q)
            + ") và " + str(stones) + " linh thạch.")
    if faction_id:
        f = db.query_one(conn, "SELECT name FROM factions WHERE id=?", (faction_id,))
        add_log(conn, char_id, age, "the_luc",
                "Với thân phận đệ tử ngoại môn, ngươi gia nhập " + f["name"] + ".")
    return char_id


# ==================== TAI TRANG THAI ====================
def load_full_state(conn, char_id):
    char = get_character(conn, char_id)
    inv = db.query(conn, "SELECT * FROM inventory WHERE character_id=? AND quantity>0 ORDER BY id", (char_id,))
    npcs = db.query(conn, "SELECT * FROM npcs WHERE character_id=? ORDER BY ABS(relationship_value) DESC, id", (char_id,))
    factions = db.query(conn, "SELECT * FROM factions WHERE character_id=? ORDER BY id", (char_id,))
    logs = db.query(conn, "SELECT age, event_type, content FROM log_entries WHERE character_id=? "
                          "ORDER BY id DESC LIMIT 300", (char_id,))
    logs.reverse()
    member = None
    if char["faction_id"]:
        member = next((f for f in factions if f["id"] == char["faction_id"]), None)
    cv = cultivation_view(char)
    life = total_lifespan(char)
    return {
        "character": public_char(char),
        "cultivation": cv,
        "lifespan": {"age": char["age"], "lifespan": life, "remaining": life - char["age"]},
        "time_step_years": TIME_STEP_YEARS[char["realm_index"]],
        "currency": {"linh_thach": char["spirit_stones"]},
        "inventory": inv,
        "npcs": [npc_public(n) for n in npcs],
        "factions": factions,
        "member_faction": member,
        "pending_event": json.loads(char["pending_event"]) if char["pending_event"] else None,
        "log": logs,
        "alive": bool(char["alive"]),
        "death": ({"cause": char["death_cause"], "age": char["death_age"]}
                  if not char["alive"] else None),
        "saved_at": char["updated_at"],
        "ai_configured": aisvc.is_configured(),
    }


# ==================== LUAT TU LUYEN ====================
def yearly_progress(char, mult=1.0):
    base = 1.2 / (1 + char["realm_index"])
    root = max(0.3, min(2.5, float(char["root_mult"] or 1.0)))
    apt = 0.6 + char["aptitude"] / 100.0 * 0.9
    tech = 0.5 + char["technique_quality"] * 0.25
    mind = 0.5 + char["mind"] / 200.0
    health = 0.3 + char["health"] / 100.0 * 0.7
    pen = 1.0
    for s in char["statuses"]:
        if s == "trọng thương":
            pen *= 0.35
        elif s == "tâm ma":
            pen *= 0.5
        elif s == "trung độc":
            pen *= 0.7
        elif s == "kiệt sức":
            pen *= 0.6
        elif s == "bị truy sát":
            pen *= 0.8
    return base * root * apt * tech * mind * health * pen * mult


def _add_progress(char, amount):
    """Cong tien do tu vi (toi da 12). Tra ve chuoi moc tu vi neu len bac."""
    old_bac = max(1, min(10, int(char["progress"])))
    char["progress"] = min(MAX_PROGRESS, float(char["progress"]) + amount)
    new_bac = max(1, min(10, int(char["progress"])))
    if new_bac > old_bac:
        stage = STAGES[min(3, (new_bac - 1) // 3)]
        return "Tu vi đạt " + REALMS[char["realm_index"]] + " Bậc " + str(new_bac) + " — " + stage + "."
    return None


def _persist_character(conn, c):
    st = c["statuses"]
    if isinstance(st, list):
        st = json.dumps(st, ensure_ascii=False)
    conn.execute(
        """UPDATE characters SET age=?, health=?, mind=?, reputation=?, spirit_stones=?,
           realm_index=?, progress=?, statuses=?, faction_id=?, technique_name=?,
           technique_quality=?, extra_lifespan=?, spirit_sense=?, alive=?, death_cause=?,
           death_age=?, pending_event=?, updated_at=? WHERE id=?""",
        (c["age"], c["health"], c["mind"], c["reputation"], c["spirit_stones"],
         c["realm_index"], c["progress"], st, c["faction_id"], c["technique_name"],
         c["technique_quality"], c["extra_lifespan"], c["spirit_sense"], int(bool(c["alive"])),
         c["death_cause"], c["death_age"], c["pending_event"], db.now_str(), c["id"]))


def _set_pending(conn, char_id, pending):
    conn.execute("UPDATE characters SET pending_event=? WHERE id=?",
                 (json.dumps(pending, ensure_ascii=False), char_id))


def _die(conn, char, cause):
    char["alive"] = 0
    char["death_cause"] = cause
    char["death_age"] = char["age"]
    char["pending_event"] = None
    _persist_character(conn, char)
    add_log(conn, char["id"], char["age"], "sinh_tu",
            "Ngươi đã qua đời ở tuổi " + str(char["age"]) + ". Nguyên nhân: " + cause + ".")


def _simulate_one_year(sim, mult):
    notes = []
    statuses = sim["statuses"]
    if "trung độc" in statuses:
        sim["health"] = max(0.0, sim["health"] - 3)
        if random.random() < 0.3:
            statuses.remove("trung độc")
            notes.append("độc tính trong người tan dần")
    if "trọng thương" in statuses and random.random() < 0.25:
        statuses.remove("trọng thương")
        notes.append("vết thương dần hồi phục")
    if "tâm ma" in statuses and random.random() < 0.2:
        statuses.remove("tâm ma")
        notes.append("tâm ma được hóa giải")
    if "kiệt sức" in statuses:
        statuses.remove("kiệt sức")
    sim["health"] = min(100.0, sim["health"] + (1.0 if "trọng thương" in statuses else 2.5))
    sim["mind"] = min(100.0, sim["mind"] + 1.0)
    gain = yearly_progress(sim, mult)
    milestone = _add_progress(sim, gain)
    line = random.choice(QUIET_YEAR_LINES)
    if random.random() < 0.10:
        line += " " + random.choice(FLAVOR_LINES)
    if milestone:
        line += " " + milestone
    if notes:
        line += " (" + "; ".join(notes) + ")"
    return line


def advance_time(conn, char_id, mode="normal"):
    """Tien thoi gian tung nam mot. Neu co bien co AI thi goi AI TRUOC khi ghi du lieu:
    neu AI that bai, khong thay doi trang thai nao (giao dich nguyen ven)."""
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời, không thể tiếp tục.")
    if char["pending_event"]:
        raise GameError("Đang có biến cố chờ lựa chọn. Hãy xử lý trước.")
    years = TIME_STEP_YEARS[char["realm_index"]]
    if mode == "cultivate":
        years, event_prob, mult = 1, 0.25, 1.0
    elif mode == "seclude":
        event_prob, mult = 0.12, 1.6
    else:
        event_prob, mult = 0.35, 1.0
    lifespan = total_lifespan(char)
    if char["age"] >= lifespan:
        _die(conn, char, "Đại hạn đã đến, thọ nguyên cạn kiệt.")
        return {"died": True, "years": 0, "event": None, "new_age": char["age"]}
    eff_years = max(1, min(years, lifespan - char["age"]))
    trigger = random.random() < event_prob and aisvc.is_configured()
    event_offset = random.randint(1, eff_years) if trigger else None

    sim = dict(char)
    year_lines = []
    died = False
    ran = 0
    for y in range(1, eff_years + 1):
        if sim["age"] >= lifespan:
            died = True
            break
        sim["age"] += 1
        ran = y
        line = _simulate_one_year(sim, mult)
        year_lines.append((sim["age"], line))
        if event_offset == y:
            break
    if sim["age"] >= lifespan:
        died = True

    event = None
    pending = None
    if not died and event_offset is not None and event_offset <= ran:
        context = build_ai_context(conn, sim)
        instruction = ("Nhân vật đang trong khoảng thời gian " +
                       ("bế quan tu luyện" if mode == "seclude" else "tu luyện sinh hoạt thường ngày") +
                       ". Hãy tạo một biến cố xen vào năm thứ " + str(event_offset) +
                       " của khoảng thời gian này, gắn với tuổi " + str(sim["age"]) + " của nhân vật.")
        event = aisvc.generate_event(context, instruction)
        pending = {"event": event,
                   "_meta": {"age": sim["age"], "source": "time_" + mode, "created": db.now_str()}}

    # Commit mot giao dich nguyen ven
    _persist_character(conn, sim)
    for age, line in year_lines:
        add_log(conn, char_id, age, "tu_luyen", line)
    if pending is not None:
        _set_pending(conn, char_id, pending)
        add_log(conn, char_id, pending["_meta"]["age"], "bien_co", event["narrative"])
    if died:
        _die(conn, sim, "Đại hạn đã đến, thọ nguyên cạn kiệt.")
    return {"died": died, "years": ran, "event": event, "new_age": sim["age"]}


# ==================== HANH DONG ====================
def _req_no_faction(conn, char):
    if char["faction_id"]:
        f = db.query_one(conn, "SELECT name FROM factions WHERE id=?", (char["faction_id"],))
        raise GameError("Ngươi đang thuộc " + (f["name"] if f else "một thế lực")
                        + ". Hãy rời khỏi thế lực này trước.")


def _req_has_faction(conn, char):
    if not char["faction_id"]:
        raise GameError("Ngươi chưa gia nhập thế lực nào.")


def _req_found_resources(conn, char):
    if char["spirit_stones"] < 500:
        raise GameError("Thành lập thế lực cần 500 linh thạch (ngươi có " + str(char["spirit_stones"]) + ").")
    if char["reputation"] < 20:
        raise GameError("Danh tiếng chưa đủ để chiêu mộ người theo (cần 20, hiện " + str(int(char["reputation"])) + ").")


def _req_has_enemy(conn, char):
    row = db.query_one(conn, "SELECT name FROM npcs WHERE character_id=? AND alive=1 AND relationship_value<=-60",
                       (char["id"],))
    if not row:
        raise GameError("Chưa có kẻ thù nào thâm thù đủ để trả thù.")


def _req_has_npc(conn, char):
    row = db.query_one(conn, "SELECT name FROM npcs WHERE character_id=? AND alive=1", (char["id"],))
    if not row:
        raise GameError("Ngươi chưa quen biết ai để kết giao.")


def _req_realm_ket_dan(conn, char):
    if char["realm_index"] < 2:
        raise GameError("Cần tu vi tối thiểu Kết Đan mới đủ tư cách nhận đệ tử.")


REQUIRES = {
    "no_faction": _req_no_faction,
    "has_faction": _req_has_faction,
    "found_resources": _req_found_resources,
    "has_enemy": _req_has_enemy,
    "has_npc": _req_has_npc,
    "realm_ket_dan": _req_realm_ket_dan,
}


def build_ai_context(conn, char):
    logs_events = db.query(conn, "SELECT content FROM log_entries WHERE character_id=? AND event_type='bien_co' "
                                 "ORDER BY id DESC LIMIT 5", (char["id"],))
    recent_logs = db.query(conn, "SELECT age, event_type, content FROM log_entries WHERE character_id=? "
                                 "ORDER BY id DESC LIMIT 8", (char["id"],))
    npcs = db.query(conn, "SELECT name, identity, realm_index, progress, personality, goal, "
                          "relationship_value, role FROM npcs WHERE character_id=? AND alive=1 "
                          "ORDER BY ABS(relationship_value) DESC LIMIT 8", (char["id"],))
    factions = db.query(conn, "SELECT name, type, leader, reputation, power_realm, territory, description "
                              "FROM factions WHERE character_id=?", (char["id"],))
    inv = db.query(conn, "SELECT name, item_type, quality, quantity FROM inventory WHERE character_id=? "
                         "AND quantity>0 ORDER BY id DESC LIMIT 12", (char["id"],))
    member = None
    if char["faction_id"]:
        member = db.query_one(conn, "SELECT name, type FROM factions WHERE id=?", (char["faction_id"],))
    cv = cultivation_view(char)
    return {
        "nhan_vat": {
            "ten": char["name"], "gioi_tinh": char["gender"], "tuoi": char["age"],
            "xuat_than": char["origin_label"], "linh_can": char["root_name"],
            "tu_chat": char["aptitude"], "ngo_tinh": char["comprehension"],
            "can_cot": char["bone"], "khi_van": char["luck"], "mi_luc": char["charm"],
            "than_thuc": char["spirit_sense"], "suc_khoe": round(char["health"]),
            "tam_canh": round(char["mind"]), "danh_tieng": round(char["reputation"]),
            "cong_phap": char["technique_name"] + " (phẩm " + str(char["technique_quality"]) + ")",
            "the_luc": (member["name"] if member else "tán tu, chưa gia nhập thế lực nào"),
            "trang_thai": char["statuses"],
        },
        "tu_vi": {"dai_canh_gioi": cv["realm_name"], "bac": cv["level"],
                  "tieu_canh_gioi": cv["stage"], "tien_do": str(cv["progress"]) + "/12"},
        "tai_san": {"linh_thach": char["spirit_stones"],
                    "tui_do": [{"ten": i["name"], "loai": i["item_type"], "pham": i["quality"],
                                "so_luong": i["quantity"]} for i in inv]},
        "the_luc_trong_the_gioi": [{"ten": f["name"], "loai": f["type"], "dau_linh": f["leader"],
                                    "danh_tieng": f["reputation"], "luc_luong": REALMS[f["power_realm"]],
                                    "dia_ban": f["territory"], "mo_ta": f["description"]} for f in factions],
        "npc_quan_trong": [{"ten": n["name"], "than_phan": n["identity"],
                            "tu_vi": REALMS[n["realm_index"]], "tinh_cach": n["personality"],
                            "muc_tieu": n["goal"], "quan_he": rel_label(n["relationship_value"]),
                            "vai_tro": n["role"]} for n in npcs],
        "nhat_ky_gan_day": [{"tuoi": l["age"], "loai": l["event_type"], "noi_dung": l["content"]}
                            for l in recent_logs],
        "bien_co_gan_day_de_tranh_lap": [l["content"] for l in logs_events],
        "goi_y_chu_de": random.choice(THEMES),
    }


def generate_action_event(conn, char_id, action_key, free_text=None):
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời.")
    if char["pending_event"]:
        raise GameError("Đang có biến cố chờ lựa chọn. Hãy xử lý trước.")
    if free_text:
        action_key = "free"
        instruction = ("Người chơi nhập hành động tự do: \"" + free_text[:300] + "\". "
                       "Hãy diễn giải ý định này thành một biến cố. Nếu hành động vượt quá khả năng "
                       "hiện tại của nhân vật, hãy để biến cố giải thích ngắn gọn vì sao không khả thi "
                       "và đưa ra các lựa chọn thay thế hợp lý; tuyệt đối không cho phép hành động "
                       "bất khả thi thành công.")
    else:
        action = ACTIONS.get(action_key)
        if not action:
            raise GameError("Hành động không tồn tại.")
        if action["kind"] != "ai":
            raise GameError("Hành động này được hệ thống xử lý trực tiếp, không cần tạo biến cố.")
        req = action.get("requires")
        if req and req in REQUIRES:
            REQUIRES[req](conn, char)
        instruction = ("Hành động của nhân vật: " + action["label"] + ". " + action["hint"]
                       + " Hãy tạo một biến cố mở đầu cho hành động này.")
    context = build_ai_context(conn, char)
    event = aisvc.generate_event(context, instruction)
    pending = {"event": event,
               "_meta": {"age": char["age"], "source": action_key, "free_text": free_text,
                         "created": db.now_str()}}
    _set_pending(conn, char_id, pending)
    add_log(conn, char_id, char["age"], "bien_co", event["narrative"])
    return event


# ==================== CHIEN DAU ====================
def combat_power(char, equipped_quality=0):
    base = (char["realm_index"] * 12 + char["progress"]) * 8
    base += char["technique_quality"] * 10
    base += char["spirit_sense"] * 0.4
    base += char["health"] * 0.3
    base += char["mind"] * 0.1
    base += equipped_quality * 12
    base *= 1.0 + (char["aptitude"] - 50) / 400.0
    return base


def _combat_verdict(conn, char, opponents):
    """Quy dinh chien dau - thuc thi bang code:
    - Chenh lech 2 tieu canh gioi tro len: KHONG THE thang tran chien truc dien cong bang.
    - Chenh lech 1 tieu canh gioi: co the thang neu co loi the (cong phap, phap bao, thien phu).
    - Thua co the chet; may man cao co the thoat than mang trong thuong.
    """
    opps = []
    for o in opponents[:3]:
        ri = int(max(0, min(7, int(o.get("realm_index", char["realm_index"])))))
        ri = min(ri, char["realm_index"] + 1)  # doi thu toi da cao hon 1 dai canh gioi
        try:
            pr = float(max(1.0, min(12.0, float(o.get("progress", 1)))))
        except (TypeError, ValueError):
            pr = 1.0
        opps.append({"name": str(o.get("name", ""))[:40] or "kẻ địch", "ri": ri, "pr": pr})
    if not opps:
        return None
    main = max(opps, key=lambda x: x["ri"] * 12 + x["pr"])
    p_tier = tier_of(char["realm_index"], char["progress"])
    o_tier = tier_of(main["ri"], main["pr"])
    eq = db.query_one(conn, "SELECT quality FROM inventory WHERE character_id=? AND equipped=1", (char["id"],))
    p_pow = combat_power(char, eq["quality"] if eq else 0)
    o_pow = ((main["ri"] * 12 + main["pr"]) * 8) * (1 + 0.25 * (len(opps) - 1))
    diff = o_tier - p_tier
    if diff >= 2:
        win_p = 0.0  # vuot 2 tieu canh gioi: khong the thang tran cong bang
    elif diff == 1:
        win_p = min(0.45, 0.08 + max(0.0, (p_pow - 0.9 * o_pow)) / max(o_pow, 1.0))
    else:
        win_p = 0.55 + (p_pow - o_pow) / max(o_pow, 1.0) * 0.6
    win_p += (char["luck"] - 50) / 1000.0
    win_p = max(0.0, min(0.95, win_p))

    if random.random() < win_p:
        dmg = random.randint(4, 14)
        stones = random.randint((o_tier + 1) * 4, (o_tier + 1) * 12)
        return {"result": "win", "text": "thắng lợi", "health_delta": -dmg,
                "stones_delta": stones,
                "status_add": (["trọng thương"] if dmg >= 12 else []),
                "opponent": main["name"], "death_cause": None,
                "note": "Ngươi thắng " + main["name"] + " trong trận đấu trực diện, thu "
                        + str(stones) + " linh thạch chiến lợi phẩm."}
    dmg = 20 + max(0, diff) * 12 + random.randint(0, 15)
    new_health = char["health"] - dmg
    if new_health <= 0:
        escape_p = 0.3 + char["luck"] / 300.0
        if random.random() < escape_p:
            return {"result": "flee", "text": "thoát thân trong ngàn cân treo sợi tóc",
                    "health_delta": -(char["health"] - 3), "stones_delta": 0,
                    "status_add": ["trọng thương"], "opponent": main["name"], "death_cause": None,
                    "note": "Ngươi thua trước " + main["name"]
                            + " và mang trọng thương chạy trốn trong đường tơ kẽ tóc."}
        return {"result": "death", "text": "tử vong", "health_delta": -char["health"],
                "stones_delta": 0, "status_add": [], "opponent": main["name"],
                "death_cause": "Chết dưới tay " + main["name"] + " trong một trận chiến trực diện.",
                "note": "Ngươi thất bại trước " + main["name"] + " và bỏ mạng tại chỗ."}
    return {"result": "lose", "text": "thất bại", "health_delta": -dmg, "stones_delta": 0,
            "status_add": (["trọng thương"] if dmg >= 30 else []), "opponent": main["name"],
            "death_cause": None,
            "note": "Ngươi thua trước " + main["name"] + ", mang thương tích rời đi."}


def _merge_verdict(effects, verdict):
    e = dict(effects) if isinstance(effects, dict) else {}
    try:
        ai_stones = float(e.get("spirit_stones_delta") or 0)
    except (TypeError, ValueError):
        ai_stones = 0.0
    e["spirit_stones_delta"] = ai_stones + verdict.get("stones_delta", 0)
    e["health_delta"] = verdict.get("health_delta", 0)
    sa = e.get("status_add")
    if not isinstance(sa, list):
        sa = []
    e["status_add"] = sa + list(verdict.get("status_add") or [])
    e["player_death"] = verdict.get("result") == "death"
    return e


# ==================== AP DUNG HIEU UNG (KIEM TRA DU LIEU AI) ====================
def apply_effects(conn, char, effects):
    """Kiem tra va ap dung hieu ung AI de xuat. Moi gia tri deu bi gioi han.
    Tra ve (summary, notes, death). Ghi log cho tung thay doi quan trong."""
    notes = []
    summary = []
    if not isinstance(effects, dict):
        effects = {}
    age = char["age"]

    def num(key, lo, hi, default=0):
        v = effects.get(key, default)
        if isinstance(v, bool):
            return float(default)
        try:
            v = float(v)
        except (TypeError, ValueError):
            return float(default)
        return max(lo, min(hi, v))

    hd = num("health_delta", -60, 60)
    if abs(hd) >= 1:
        before = char["health"]
        char["health"] = clamp(char["health"] + hd, 0, 100)
        summary.append("Sức khỏe " + format(char["health"] - before, "+.0f"))
    md = num("mind_delta", -40, 40)
    if abs(md) >= 1:
        before = char["mind"]
        char["mind"] = clamp(char["mind"] + md, 0, 100)
        summary.append("Tâm cảnh " + format(char["mind"] - before, "+.0f"))
    rd = num("reputation_delta", -50, 50)
    if abs(rd) >= 1:
        char["reputation"] = clamp(char["reputation"] + rd, -100, 1000)
        summary.append("Danh tiếng " + format(rd, "+.0f"))
    ld = num("lifespan_delta", -50, 100)
    if abs(ld) >= 1:
        char["extra_lifespan"] += int(ld)
        summary.append("Thọ nguyên " + format(int(ld), "+d") + " năm")
        add_log(conn, char["id"], age, "he_thong",
                "Thọ nguyên của ngươi thay đổi " + format(int(ld), "+d") + " năm.")
    pd_ = num("cultivation_progress_delta", -6, 6)
    if abs(pd_) >= 0.5:
        if pd_ > 0:
            m = _add_progress(char, pd_)
            summary.append("Tu vi +" + format(pd_, ".1f"))
            if m:
                add_log(conn, char["id"], age, "tu_luyen", m)
        else:
            char["progress"] = max(1.0, char["progress"] + pd_)
            summary.append("Tu vi " + format(pd_, ".1f"))
    sd = int(num("spirit_stones_delta", -200000, 200000))
    if sd != 0:
        if sd < 0 and char["spirit_stones"] + sd < 0:
            notes.append("Giao dịch bị hệ thống điều chỉnh: ngươi chỉ có "
                         + str(char["spirit_stones"]) + " linh thạch, không đủ cho khoản chi "
                         + str(abs(sd)) + ".")
            sd = -char["spirit_stones"]
        char["spirit_stones"] += sd
        summary.append(format(sd, "+d") + " linh thạch")
        add_log(conn, char["id"], age, "giao_dich",
                ("Nhận " if sd > 0 else "Tiêu hao ") + str(abs(sd)) + " linh thạch.")

    sa = effects.get("status_add") or []
    if isinstance(sa, list):
        for s in sa[:3]:
            s = str(s).strip().lower()
            if s in STATUS_LIST and s not in char["statuses"]:
                char["statuses"].append(s)
                summary.append("Rơi vào: " + s)
                add_log(conn, char["id"], age, "he_thong", "Ngươi rơi vào trạng thái: " + s + ".")
    sr = effects.get("status_remove") or []
    if isinstance(sr, list):
        for s in sr[:3]:
            s = str(s).strip().lower()
            if s in char["statuses"]:
                char["statuses"].remove(s)
                summary.append("Hết: " + s)

    adds = effects.get("add_items") or []
    if isinstance(adds, list):
        for it in adds[:3]:
            if not isinstance(it, dict):
                continue
            name = str(it.get("name", "")).strip()[:40]
            if not name:
                continue
            itype = str(it.get("item_type", "tạp vật")).strip().lower()
            if itype not in ITEM_TYPES:
                itype = "tạp vật"
            try:
                q = int(clamp(int(it.get("quality", 1)), 1, 5))
            except (TypeError, ValueError):
                q = 1
            try:
                qty = int(clamp(int(it.get("quantity", 1)), 1, 5))
            except (TypeError, ValueError):
                qty = 1
            desc = str(it.get("description", ""))[:120]
            existing = db.query_one(conn, "SELECT id FROM inventory WHERE character_id=? AND name=?",
                                    (char["id"], name))
            if existing:
                conn.execute("UPDATE inventory SET quantity=quantity+? WHERE id=?", (qty, existing["id"]))
            else:
                conn.execute(
                    """INSERT INTO inventory (character_id, name, item_type, quality, quantity,
                       description, usable_key, equipped) VALUES (?,?,?,?,?,?,?,0)""",
                    (char["id"], name, itype, q, qty, desc, match_pill(name)))
            summary.append("+ " + name + " x" + str(qty))
            add_log(conn, char["id"], age, "vat_pham",
                    "Nhận " + name + " x" + str(qty) + " (" + itype + ", phẩm " + str(q) + ").")

    rems = effects.get("remove_items") or []
    if isinstance(rems, list):
        for it in rems[:3]:
            if not isinstance(it, dict):
                continue
            name = str(it.get("name", "")).strip()[:40]
            if not name:
                continue
            try:
                qty = int(clamp(int(it.get("quantity", 1)), 1, 20))
            except (TypeError, ValueError):
                qty = 1
            row = db.query_one(conn, "SELECT id, name, quantity FROM inventory WHERE character_id=? "
                                     "AND name LIKE ? AND quantity>0", (char["id"], "%" + name + "%"))
            if not row:
                notes.append("Không tìm thấy \"" + name + "\" trong túi đồ để tiêu hao; hệ thống bỏ qua.")
                continue
            take = min(qty, row["quantity"])
            _consume_item(conn, row["id"], take)
            summary.append("- " + row["name"] + " x" + str(take))
            add_log(conn, char["id"], age, "vat_pham", "Tiêu hao " + row["name"] + " x" + str(take) + ".")

    news = effects.get("new_npcs") or []
    if isinstance(news, list):
        for n in news[:2]:
            if not isinstance(n, dict):
                continue
            name = str(n.get("name", "")).strip()[:30]
            if not name:
                continue
            if db.query_one(conn, "SELECT id FROM npcs WHERE character_id=? AND name=?", (char["id"], name)):
                notes.append("NPC \"" + name + "\" đã tồn tại; hệ thống không tạo trùng.")
                continue
            try:
                ri = int(clamp(int(n.get("realm_index", char["realm_index"])), 0, min(7, char["realm_index"] + 2)))
            except (TypeError, ValueError):
                ri = char["realm_index"]
            try:
                pr = float(clamp(float(n.get("progress", 1)), 1.0, 12.0))
            except (TypeError, ValueError):
                pr = 1.0
            rel = str(n.get("relationship", "xa lạ")).strip().lower()
            rv = REL_LABELS.get(rel, 8.0)
            conn.execute(
                """INSERT INTO npcs (character_id, name, identity, realm_index, progress, personality,
                   goal, relationship_value, role, alive, created_age) VALUES (?,?,?,?,?,?,?,?,?,1,?)""",
                (char["id"], name, str(n.get("identity", "Tán tu"))[:80], ri, pr,
                 str(n.get("personality", ""))[:80], str(n.get("goal", ""))[:80], rv, rel, age))
            summary.append("Gặp gỡ: " + name)
            add_log(conn, char["id"], age, "xa_giao",
                    "Lần đầu gặp " + name + " — " + str(n.get("identity", "Tán tu"))[:60]
                    + " (" + REALMS[ri] + ").")

    rcs = effects.get("relationship_changes") or []
    if isinstance(rcs, list):
        for rc in rcs[:4]:
            if not isinstance(rc, dict):
                continue
            name = str(rc.get("name", "")).strip()[:30]
            try:
                delta = float(clamp(float(rc.get("delta", 0)), -50.0, 50.0))
            except (TypeError, ValueError):
                delta = 0.0
            if not name or abs(delta) < 1:
                continue
            npc = db.query_one(conn, "SELECT id, name, relationship_value, alive FROM npcs "
                                     "WHERE character_id=? AND name LIKE ?", (char["id"], "%" + name + "%"))
            if not npc or not npc["alive"]:
                notes.append("Không tìm thấy NPC \"" + name + "\" để thay đổi quan hệ; hệ thống bỏ qua.")
                continue
            nv = clamp(npc["relationship_value"] + delta, -100, 100)
            conn.execute("UPDATE npcs SET relationship_value=? WHERE id=?", (nv, npc["id"]))
            summary.append("Quan hệ với " + npc["name"] + " " + format(delta, "+.0f")
                          + " (" + rel_label(nv) + ")")
            add_log(conn, char["id"], age, "xa_giao",
                    "Quan hệ với " + npc["name"] + " " + format(delta, "+.0f")
                    + " (hiện là: " + rel_label(nv) + ").")

    deaths = effects.get("npc_deaths") or []
    if isinstance(deaths, list):
        for name in deaths[:2]:
            name = str(name).strip()[:30]
            if not name:
                continue
            npc = db.query_one(conn, "SELECT id, name, alive FROM npcs WHERE character_id=? AND name LIKE ?",
                               (char["id"], "%" + name + "%"))
            if not npc:
                notes.append("Không tìm thấy NPC \"" + name + "\"; không thể ghi nhận tử vong.")
                continue
            if not npc["alive"]:
                continue
            conn.execute("UPDATE npcs SET alive=0 WHERE id=?", (npc["id"],))
            summary.append(npc["name"] + " đã qua đời")
            add_log(conn, char["id"], age, "sinh_tu", npc["name"] + " đã tử vong.")

    st = effects.get("set_technique")
    if isinstance(st, dict):
        tname = str(st.get("name", "")).strip()[:40]
        try:
            tq = int(clamp(int(st.get("quality", 1)), 1, 5))
        except (TypeError, ValueError):
            tq = 1
        if tname:
            char["technique_name"] = tname
            char["technique_quality"] = tq
            summary.append("Công pháp: " + tname + " (phẩm " + str(tq) + ")")
            add_log(conn, char["id"], age, "tu_luyen",
                    "Ngươi chuyển sang tu luyện " + tname + " (phẩm " + str(tq) + ").")

    jf = effects.get("join_faction")
    if isinstance(jf, str) and jf.strip():
        fname = jf.strip()
        fac = db.query_one(conn, "SELECT id, name FROM factions WHERE character_id=? AND name LIKE ?",
                           (char["id"], "%" + fname + "%"))
        if char["faction_id"]:
            notes.append("Ngươi đã thuộc một thế lực; muốn gia nhập thế lực mới phải rời trước.")
        elif fac:
            char["faction_id"] = fac["id"]
            summary.append("Gia nhập " + fac["name"])
            add_log(conn, char["id"], age, "the_luc", "Ngươi chính thức gia nhập " + fac["name"] + ".")
        else:
            notes.append("Thế lực \"" + fname + "\" không tồn tại trong thế giới; hệ thống bỏ qua.")
    if effects.get("leave_faction"):
        if char["faction_id"]:
            fac = db.query_one(conn, "SELECT name FROM factions WHERE id=?", (char["faction_id"],))
            char["faction_id"] = None
            char["reputation"] = max(-100.0, char["reputation"] - 5)
            summary.append("Rời khỏi " + (fac["name"] if fac else "thế lực cũ"))
            add_log(conn, char["id"], age, "the_luc",
                    "Ngươi rời khỏi " + (fac["name"] if fac else "thế lực cũ") + ".")
        else:
            notes.append("Ngươi chưa gia nhập thế lực nào nên không thể rời khỏi.")
    ff = effects.get("found_faction")
    if isinstance(ff, dict) and str(ff.get("name", "")).strip():
        fname = str(ff["name"]).strip()[:40]
        ftype = str(ff.get("type", "Thế lực tán tu")).strip()[:40]
        if char["faction_id"]:
            notes.append("Phải rời khỏi thế lực hiện tại trước khi thành lập thế lực riêng.")
        elif char["spirit_stones"] < 500:
            notes.append("Không đủ linh thạch để thành lập thế lực (cần 500, ngươi có "
                         + str(char["spirit_stones"]) + ").")
        elif char["reputation"] < 20:
            notes.append("Danh tiếng chưa đủ để chiêu mộ người (cần 20, hiện "
                         + str(int(char["reputation"])) + ").")
        elif db.query_one(conn, "SELECT id FROM factions WHERE character_id=? AND name=?",
                          (char["id"], fname)):
            notes.append("Thế lực \"" + fname + "\" đã tồn tại.")
        else:
            char["spirit_stones"] -= 500
            fid = db.execute(
                conn,
                """INSERT INTO factions (character_id, name, type, leader, resources, reputation,
                   power_realm, territory, description, is_player_founded) VALUES (?,?,?,?,?,?,?,?,?,1)""",
                (char["id"], fname, ftype, char["name"], "Vật liệu sơ khai",
                 max(0, char["reputation"]), char["realm_index"], "Chưa có địa bàn",
                 "Thế lực do ngươi sáng lập."))
            char["faction_id"] = fid
            summary.append("Thành lập " + fname + " (-500 linh thạch)")
            add_log(conn, char["id"], age, "the_luc",
                    "Ngươi tiêu 500 linh thạch thành lập thế lực " + fname
                    + ", tự nhận làm người đứng đầu.")

    death = False
    allow = (char["health"] <= 0) or (char["age"] >= total_lifespan(char))
    want_death = bool(effects.get("player_death"))
    if want_death and allow:
        death = True
    elif want_death:
        char["health"] = max(1.0, char["health"])
        notes.append("AI đề nghị nhân vật tử vong nhưng hệ thống xác định chưa đủ điều kiện; "
                     "ngươi thoát chết trong đường tơ kẽ tóc.")
    if char["health"] <= 0:
        death = True
    return summary, notes, death


def resolve_event(conn, char_id, choice_id):
    """Phan giai lua chon: AI ke ket qua, engine kiem tra hieu ung roi moi ghi du lieu."""
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời.")
    raw = char["pending_event"]
    if not raw:
        raise GameError("Không có biến cố đang chờ lựa chọn.")
    pending = json.loads(raw)
    event = pending["event"]
    meta = pending["_meta"]
    cid = str(choice_id or "").strip().upper()
    choice = None
    for ch in event.get("choices", []):
        if str(ch.get("id", "")).strip().upper() == cid:
            choice = ch
            break
    if choice is None:
        raise GameError("Lựa chọn không hợp lệ.")

    verdict = None
    if choice.get("combat") and event.get("opponents"):
        verdict = _combat_verdict(conn, char, event["opponents"])

    context = build_ai_context(conn, char)
    context["event"] = {"narrative": event["narrative"], "event_type": event.get("event_type", "misc")}
    context["choice"] = {"id": choice.get("id"), "label": choice.get("label"),
                         "description": choice.get("description")}
    if verdict:
        context["combat_verdict"] = verdict

    outcome = aisvc.resolve_choice(context)
    effects = outcome.get("effects") or {}
    if verdict:
        effects = _merge_verdict(effects, verdict)

    age = int(meta.get("age", char["age"]))
    summary, notes, death = apply_effects(conn, char, effects)
    outcome_text = outcome.get("outcome", "")

    if verdict:
        add_log(conn, char_id, age, "chien_dau", verdict["note"])
    log_content = outcome_text + ((" | " + "; ".join(summary)) if summary else "")
    add_log(conn, char_id, age, "bien_co", log_content)
    for n in notes:
        add_log(conn, char_id, age, "he_thong", "Hệ thống: " + n)

    char["pending_event"] = None
    if death:
        cause = (verdict.get("death_cause") if verdict and verdict.get("death_cause")
                else "Thương thế quá nặng, ngươi kiệt sức mà mất.")
        _die(conn, char, cause)
    else:
        _persist_character(conn, char)
    return {"outcome": outcome_text, "summary": summary, "notes": notes, "died": death}


# ==================== HANH DONG ENGINE (KHONG CAN AI) ====================
def attempt_breakthrough(conn, char_id):
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời.")
    if char["pending_event"]:
        raise GameError("Hãy xử lý biến cố đang chờ trước.")
    if char["realm_index"] >= 7 and char["progress"] >= MAX_PROGRESS:
        raise GameError("Đại Thừa Đại Viên Mãn là đỉnh cao của thế giới này. "
                        "Con đường phi thăng sẽ được mở ra trong tương lai.")
    if char["progress"] < MAX_PROGRESS:
        raise GameError("Tu vi chưa đạt Đại Viên Mãn trọn vẹn (tiến độ nội bộ 3/3). "
                        "Hãy tiếp tục tu luyện.")
    chance = 0.85 - char["realm_index"] * 0.07
    chance += char["aptitude"] / 500.0
    chance += (char["technique_quality"] - 3) * 0.05
    used_pill = None
    for pill, bonus in (("Đột Phá Đan", 0.25), ("Trúc Cơ Đan", 0.15)):
        row = db.query_one(conn, "SELECT id, quantity, name FROM inventory WHERE character_id=? "
                                 "AND name LIKE ? AND quantity>0", (char_id, "%" + pill + "%"))
        if row:
            chance += bonus
            used_pill = (row["name"], row["id"])
            break
    if "trọng thương" in char["statuses"]:
        chance -= 0.15
    if "tâm ma" in char["statuses"]:
        chance -= 0.10
    chance = clamp(chance, 0.05, 0.95)
    if used_pill:
        _consume_item(conn, used_pill[1], 1)
        add_log(conn, char_id, char["age"], "vat_pham",
                "Sử dụng " + used_pill[0] + " để hỗ trợ đột phá.")
    if random.random() < chance:
        old = REALMS[char["realm_index"]]
        char["realm_index"] += 1
        char["progress"] = 1.0
        char["health"] = min(100.0, char["health"] + 10)
        char["mind"] = min(100.0, char["mind"] + 10)
        char["spirit_sense"] = 10 + char["realm_index"] * 15 + char["comprehension"] // 10
        new = REALMS[char["realm_index"]]
        add_log(conn, char_id, char["age"], "dot_pha",
                "Đột phá thành công! Từ " + old + " ngươi bước vào đại cảnh giới " + new
                + ", thọ nguyên tăng lên " + str(total_lifespan(char)) + " năm.")
        _persist_character(conn, char)
        return {"success": True, "chance": round(chance, 2), "realm": new,
                "note": "Đột phá thành công, bước vào " + new + "!"}
    char["progress"] = max(6.0, char["progress"] - 2.0)
    char["health"] = max(1.0, char["health"] - 15)
    char["mind"] = max(1.0, char["mind"] - 10)
    if random.random() < 0.25 and "tâm ma" not in char["statuses"]:
        char["statuses"].append("tâm ma")
    add_log(conn, char_id, char["age"], "dot_pha",
            "Đột phá thất bại. Linh lực tán loạn, tu vi tổn hao và ngươi chịu khổ sở "
            "(cơ hội thành công " + str(int(chance * 100)) + "%).")
    _persist_character(conn, char)
    return {"success": False, "chance": round(chance, 2), "note": "Đột phá thất bại, tu vi tụt lùi."}


def rest_action(conn, char_id):
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời.")
    if char["pending_event"]:
        raise GameError("Hãy xử lý biến cố đang chờ trước.")
    healed = 0.0
    if char["health"] < 100:
        healed = min(25.0, 100 - char["health"])
        char["health"] += healed
    char["mind"] = min(100.0, char["mind"] + 5)
    if "kiệt sức" in char["statuses"]:
        char["statuses"].remove("kiệt sức")
    add_log(conn, char_id, char["age"], "he_thong",
            ("Nghỉ ngơi dưỡng thương: sức khỏe +" + str(int(healed)) + ", tâm cảnh +5.")
            if healed else "Nghỉ ngơi lấy lại tinh thần.")
    _persist_character(conn, char)
    return {"note": "Đã nghỉ ngơi dưỡng thương."}


def calm_mind_action(conn, char_id):
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời.")
    if char["pending_event"]:
        raise GameError("Hãy xử lý biến cố đang chờ trước.")
    statuses = char["statuses"]
    if "tâm ma" in statuses:
        if random.random() < 0.6 + char["mind"] / 250.0:
            statuses.remove("tâm ma")
            char["mind"] = min(100.0, char["mind"] + 5)
            msg = "Tĩnh tọa bảy ngày bảy đêm, ngươi hóa giải được tâm ma."
        else:
            char["mind"] = max(1.0, char["mind"] - 3)
            msg = "Tâm ma vẫn âm ỉ chưa tan, ngươi tiêu hao tâm lực."
    elif "trọng thương" in statuses:
        char["health"] = min(100.0, char["health"] + 10)
        if random.random() < 0.4:
            statuses.remove("trọng thương")
        msg = "Ngươi vận công dưỡng thương, vết thương dần hồi phục."
    else:
        msg = "Không có tâm ma hay thương thế nào cần khắc phục. Ngươi tĩnh tọa thêm một lát."
    add_log(conn, char_id, char["age"], "tu_luyen", msg)
    _persist_character(conn, char)
    return {"note": msg}


def _consume_item(conn, item_id, qty):
    row = db.query_one(conn, "SELECT quantity FROM inventory WHERE id=?", (item_id,))
    if not row:
        return
    left = row["quantity"] - qty
    if left > 0:
        conn.execute("UPDATE inventory SET quantity=? WHERE id=?", (left, item_id))
    else:
        conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))


def use_item(conn, char_id, item_id):
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời.")
    item = db.query_one(conn, "SELECT * FROM inventory WHERE id=? AND character_id=?", (item_id, char_id))
    if not item or item["quantity"] <= 0:
        raise GameError("Vật phẩm không tồn tại trong túi đồ.")
    key = item["usable_key"]
    if not key:
        if "đột phá" in item["name"].lower() or "trúc cơ" in item["name"].lower():
            raise GameError("Đan dược này sẽ tự động được dùng khi ngươi thử đột phá.")
        raise GameError("Vật phẩm này không thể sử dụng trực tiếp.")
    eff = PILL_EFFECTS.get(key)
    if not eff:
        raise GameError("Vật phẩm này chưa có công dụng được định nghĩa.")
    parts = []
    if "health" in eff:
        before = char["health"]
        char["health"] = min(100.0, char["health"] + eff["health"])
        parts.append("sức khỏe +" + str(int(char["health"] - before)))
    if "mind" in eff:
        before = char["mind"]
        char["mind"] = min(100.0, char["mind"] + eff["mind"])
        parts.append("tâm cảnh +" + str(int(char["mind"] - before)))
    if "progress" in eff:
        m = _add_progress(char, eff["progress"])
        parts.append("tu vi tăng")
        if m:
            add_log(conn, char_id, char["age"], "tu_luyen", m)
    if "lifespan" in eff:
        char["extra_lifespan"] += eff["lifespan"]
        parts.append("thọ nguyên +" + str(eff["lifespan"]) + " năm")
    if "remove_status" in eff and eff["remove_status"] in char["statuses"]:
        char["statuses"].remove(eff["remove_status"])
        parts.append("hết " + eff["remove_status"])
    _consume_item(conn, item_id, 1)
    add_log(conn, char_id, char["age"], "vat_pham",
            "Sử dụng " + item["name"] + ": " + ", ".join(parts) + ".")
    _persist_character(conn, char)
    return {"note": "Đã dùng " + item["name"] + ": " + ", ".join(parts)}


def equip_item(conn, char_id, item_id):
    char = get_character(conn, char_id)
    if not char["alive"]:
        raise GameError("Nhân vật đã qua đời.")
    item = db.query_one(conn, "SELECT * FROM inventory WHERE id=? AND character_id=?", (item_id, char_id))
    if not item:
        raise GameError("Vật phẩm không tồn tại.")
    if item["item_type"] != "pháp bảo":
        raise GameError("Chỉ pháp bảo mới có thể trang bị.")
    if item["equipped"]:
        conn.execute("UPDATE inventory SET equipped=0 WHERE id=?", (item_id,))
        add_log(conn, char_id, char["age"], "vat_pham", "Tháo pháp bảo " + item["name"] + " ra.")
    else:
        conn.execute("UPDATE inventory SET equipped=0 WHERE character_id=?", (char_id,))
        conn.execute("UPDATE inventory SET equipped=1 WHERE id=?", (item_id,))
        add_log(conn, char_id, char["age"], "vat_pham",
                "Trang bị pháp bảo " + item["name"] + " (phẩm " + str(item["quality"]) + ").")
    return {"note": "Đã cập nhật trang bị."}
