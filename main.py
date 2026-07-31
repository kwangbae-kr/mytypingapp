import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# --- 1. 구글 시트 연동 설정 ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_google_sheet():
  try:
    # credentials.json 파일을 이용해 인증 (Streamlit Cloud에서는 Secrets 기능으로 대체 가능)
    creds = Credentials.from_service_account_file(
        "credentials.json", scopes=SCOPES
    )
    client = gspread.authorize(creds)
    # 구글 시트 이름을 본인이 만든 시트 이름으로 수정하세요!
    sheet = client.open("타자검정_기록").sheet1
    return sheet
  except Exception as e:
    st.error(
        f"구글 시트 연결에 실패했습니다. credentials.json 파일과 시트 이름을"
        f" 확인해주세요. (에러: {e})"
    )
    return None


# --- 2. Streamlit 페이지 설정 ---
st.set_page_config(
    page_title="한컴 스타일 5분 긴글 타자 검정", page_icon="⌨️", layout="centered"
)

# 세션 상태 초기화
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "student_id" not in st.session_state:
  st.session_state.student_id = ""
if "name" not in st.session_state:
  st.session_state.name = ""
if "remaining_attempts" not in st.session_state:
  st.session_state.remaining_attempts = 3
if "best_wpm" not in st.session_state:
  st.session_state.best_wpm = 0

# 긴글 연습 본문 (메밀꽃 필 무렵 일부)
TEXT_LINES = [
    "메밀꽃 필 무렵 - 이효석",
    (
        "여름 장이란 애당초에 글러서, 해는 아직 중천에 있건만 장판은 벌써"
        " 쓸쓸하고 더운 햇발이 벌여 놓은 전 휘장 밑으로 등줄기를 훅훅 볶는다."
    ),
    (
        "마월 사람들은 거지반 돌아간 뒤요, 팔리지 못한 나무꾼 패가 길거리에"
        " 궁싯거리고들 있으나, 석유병이나 받고 고깃마리나 사면 족할 이 축들을"
        " 바라고 언제까지든지 버티고 있을 법은 없다."
    ),
    (
        "춥춥스럽게 날아드는 파리 떼도 장난꾼 각다귀들도 귀찮다. 얼금뱅이요"
        " 왼손잡이인 드팀전의 허 생원은 기어코 동업의 조 선달을 나꾸어 보았다."
    ),
    "“그만 거둘까?”",
    (
        "“잘 생각했네. 봉평장에서 한 번이나 흐붓하게 사 본 일 있었을까."
        " 내일 대화장에서나 한몫 벌어야겠네.”"
    ),
]

# --- 3. 로그인 화면 ---
if not st.session_state.logged_in:
  st.title("📖 5분 긴글 타자 검정 (구글 시트 연동)")
  st.markdown("학번과 이름을 입력하고 타자 검정을 시작하세요.")

  with st.form("login_form"):
    input_id = st.text_input("학번 (4자리)", max_chars=4, placeholder="예: 1101")
    input_name = st.text_input("이름", placeholder="예: 홍길동")
    submit_btn = st.form_submit_button("검정 시작하기")

    if submit_btn:
      if not input_id.isdigit() or len(input_id) != 4:
        st.error("학번은 정확히 4자리 숫자로 입력해주세요.")
      elif not input_name.strip():
        st.error("이름을 입력해주세요.")
      else:
        sheet = get_google_sheet()
        if sheet:
          records = sheet.get_all_records()
          user_record = None

          # 기존 기록 확인
          for r in records:
            if str(r.get("student_id")) == input_id:
              user_record = r
              break

          if user_record:
            st.session_state.student_id = input_id
            st.session_state.name = input_name
            st.session_state.remaining_attempts = int(
                user_record.get("remaining_attempts", 3)
            )
            st.session_state.best_wpm = int(user_record.get("best_wpm", 0))
          else:
            # 신규 등록
            st.session_state.student_id = input_id
            st.session_state.name = input_name
            st.session_state.remaining_attempts = 3
            st.session_state.best_wpm = 0
            sheet.append_row([input_id, input_name, 0, 3])

          st.session_state.logged_in = True
          st.rerun()

# --- 4. 타자 검정 메인 화면 ---
else:
  st.subheader(
      f"👋 환영합니다, {st.session_state.student_id} {st.session_state.name}님!"
  )

  col1, col2, col3 = st.columns(3)
  col1.metric("남은 응시 기회", f"{st.session_state.remaining_attempts}회")
  col2.metric("내 최고 기록", f"{st.session_state.best_wpm} 타/분")
  col3.metric("제한 시간", "5분")

  st.divider()

  if st.session_state.remaining_attempts <= 0:
    st.error(
        "🚨 오늘 응시할 수 있는 3회의 기회를 모두 사용하셨습니다! 선생님께"
        " 문의하세요."
    )
    if st.button("로그아웃"):
      st.session_state.logged_in = False
      st.rerun()
  else:
    st.markdown("### 📝 제시문 연습 및 입력")
    st.info("아래 제시문을 보고 아래 입력창에 한 줄씩 타이핑해 주세요.")

    # 제시문 출력 박스
    for idx, line in enumerate(TEXT_LINES):
      st.text(f"[{idx+1}] {line}")

    user_full_input = st.text_area(
        "타이핑 입력 공간 (한컴타자 스타일 통합 입력)",
        height=150,
        placeholder=(
            "위 제시문 내용을 참고하여 여기에 전체 내용을 입력하거나 연습하세요."
        ),
    )

    if st.button("결과 제출하기", type="primary"):
      # 간단 타수 계산 로직 예시 (입력 글자 수 기반)
      typed_len = len(user_full_input.strip())
      # 임시 타수 환산 (5분 기준 대략적 계산 또는 글자 수 기반)
      calculated_wpm = int(typed_len * 2)

      # 최고 기록 갱신 여부 확인
      if calculated_wpm > st.session_state.best_wpm:
        st.session_state.best_wpm = calculated_wpm

      st.session_state.remaining_attempts -= 1

      # 구글 시트 업데이트
      sheet = get_google_sheet()
      if sheet:
        cell = sheet.find(str(st.session_state.student_id))
        if cell:
          row = cell.row
          # 시트 열 순서: student_id(A), name(B), best_wpm(C), remaining_attempts(D)
          sheet.update_cell(row, 3, st.session_state.best_wpm)
          sheet.update_cell(row, 4, st.session_state.remaining_attempts)

      st.success(
          f"🎉 제출 완료! (측정 타수: {calculated_wpm}타 / 최고 기록:"
          f" {st.session_state.best_wpm}타)"
      )
      st.rerun()

    if st.button("로그아웃"):
      st.session_state.logged_in = False
      st.rerun()
