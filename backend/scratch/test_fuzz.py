from rapidfuzz import fuzz

text1 = "serum dưỡng sáng hồng và làm đều màu da vùng nhạy cảm như bikini, nách, nhũ hoa, đùi trong. sản phẩm hỗ trợ cải thiện 40% tình trạng da không đều màu do ma sát, nội tiết tố hoặc phương pháp loại bỏ lông cơ học, mang lại làn da sáng mịn chuyên nghiệp."
text2 = "serum dưỡng sáng hồng và làm đều màu da vùng nhạy cảm như bikini, nách, nhũ hoa, đùi trong, sản phẩm hỗ trợ cải thiện tình trạng da không đều màu do tác động ma sát, thay đổi nội tiết tố hoặc các phương pháp loại bỏ lông cơ học. công thức đặc biệt giúp làm mờ các vùng thâm sạm, nuôi dưỡng làn da trở nên sáng mịn và đều màu hơn theo thời gian, được thiết kế chuyên biệt để đáp ứng nhu cầu chăm sóc da nhạy cảm của phụ nữ hiện đại.."

score = fuzz.ratio(text1, text2)
print("Ratio:", score)
score2 = fuzz.token_sort_ratio(text1, text2)
print("Token Sort Ratio:", score2)
