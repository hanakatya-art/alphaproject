# 2D 탱크 게임

Python과 Pygame으로 만든 간단한 탱크 사격 연습 게임입니다. 탱크를 움직이며 마우스로 조준하고, 표적 10개를 모두 파괴하면 승리합니다. 별도의 이미지나 소리 파일 없이 실행됩니다.

## 조작 방법

| 입력 | 동작 |
| --- | --- |
| `W` / `S` | 위 / 아래로 이동 |
| `A` / `D` | 왼쪽 / 오른쪽으로 이동 |
| 마우스 이동 | 포탑으로 마우스 위치 조준 |
| 마우스 왼쪽 클릭 | 포탄 발사 — 누르고 있으면 연속 발사 |
| `R` | 처음부터 다시 시작 |
| `Esc` 또는 창의 닫기 버튼 | 게임 종료 |

키가 반응하지 않으면 게임 창을 클릭해 선택하세요. 이동 키가 다르게 입력되면 한/영 입력을 영어로 바꿔 보세요.

## 처음 실행하기

이 게임은 **내 컴퓨터에서 별도의 창으로 실행하는 데스크톱 게임**입니다. 웹사이트 주소를 여는 방식이 아닙니다. 화면이 없는 클라우드 환경에서는 아래의 자동 테스트를 실행할 수 있지만 직접 플레이하려면 그래픽 화면이 있는 컴퓨터가 필요합니다.

### 1. Python과 게임 파일 준비

1. [Python 공식 사이트](https://www.python.org/downloads/)에서 Python을 설치하세요. **Python 3.12를 권장**하며, 코드에는 Python 3.10 이상이 필요합니다. Windows 설치 화면에 `Add python.exe to PATH` 항목이 있으면 체크하세요.
2. 이 프로젝트의 파일들을 컴퓨터의 한 폴더에 저장하세요. 프로젝트가 GitHub에 저장되어 있다면 저장소 페이지의 **Code → Download ZIP**으로 내려받고 압축을 풀 수 있습니다. Git 명령어를 사용할 필요는 없습니다.
3. `main.py`와 `requirements.txt`가 보이는 폴더에서 터미널을 여세요. Windows에서는 폴더의 빈 곳을 마우스 오른쪽 버튼으로 눌러 **터미널에서 열기**를 선택할 수 있습니다. macOS/Linux에서는 터미널에 `cd `를 입력한 뒤 폴더 경로를 넣고 Enter를 누르세요. 경로에 공백이 있으면 따옴표로 감싸세요.

### 2. 필요한 프로그램 설치

운영체제에 맞는 명령어를 **한 줄씩** 복사하고 Enter를 누르세요. `.venv`는 이 게임에 필요한 Python 패키지를 따로 보관하는 폴더입니다. 인터넷 연결이 필요하며, 이 설치 과정은 처음 한 번만 하면 됩니다.

**Windows**

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### 3. 게임 실행

**Windows**

```powershell
.venv\Scripts\python main.py
```

**macOS / Linux**

```bash
.venv/bin/python main.py
```

게임 창이 뜨면 바로 플레이할 수 있습니다. 다음에 다시 실행할 때는 같은 폴더에서 **게임 실행 명령만** 입력하면 됩니다. 가상 환경을 별도로 활성화할 필요는 없습니다.

## 파일 안내

| 파일 | 역할 |
| --- | --- |
| `main.py` | 게임을 시작하는 파일 |
| `tank_game.py` | 탱크 이동, 조준, 포탄, 표적, 화면을 구현한 코드 |
| `requirements.txt` | 설치할 패키지 목록 (`pygame==2.6.1`) |
| `tests/` | 게임 동작을 확인하는 자동 테스트 |
| `.gitignore` | 가상 환경 등 Git에 저장할 필요가 없는 파일 목록 |

## 자동 테스트

패키지 설치 후 프로젝트 폴더에서 실행하세요. 오류가 없다면 마지막에 `OK`가 표시됩니다.

**Windows**

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

**macOS / Linux / 클라우드 환경**

```bash
.venv/bin/python -m unittest discover -s tests -v
```

클라우드 환경에서는 `/workspace/alphaproject` 폴더에서 다음 명령으로 화면 없이 120프레임을 실행하고 마지막 화면을 이미지로 저장할 수도 있습니다.

```bash
.venv/bin/python main.py --headless --frames 120 --screenshot /tmp/tank-game.png
```

`--headless`는 자동 검사용 모드이므로 게임 창이 뜨지 않고 직접 조작할 수 없습니다. 일반 플레이에서는 이 옵션을 붙이지 마세요.

## 실행이 안 될 때

- **`py` 또는 `python3` 명령을 찾을 수 없다고 나오는 경우:** Python 설치를 확인한 뒤 터미널을 닫았다가 다시 여세요.
- **`requirements.txt`나 `main.py`를 찾을 수 없다고 나오는 경우:** 터미널이 해당 파일들이 들어 있는 폴더에 열려 있는지 확인하세요.
- **`No module named pygame`이 나오는 경우:** 위의 설치 명령을 실행한 뒤, 운영체제에 맞는 `.venv` 안의 Python으로 게임을 실행하세요.
- **Pygame 설치 중 빌드 오류가 나는 경우:** 권장 버전인 Python 3.12로 가상 환경을 만들어 설치하세요. 이미 `.venv`가 있다면 이름을 바꿔 보관한 뒤 새로 만들 수 있습니다.
- **클라우드에서 게임 창이 보이지 않는 경우:** 내 컴퓨터에서 실행하세요. 화면 없는 환경에서는 자동 테스트와 `--headless` 검사를 사용합니다.
