import textract

# PDF 파일 경로
file_path = "/Users/0heon_j/Desktop/[미국]_University_of_Texas_at_Austin_신O준.hwp"

# PDF 파일에서 텍스트 추출
text = textract.process(file_path)

# 텍스트 출력
print(text.decode("utf-8"))
