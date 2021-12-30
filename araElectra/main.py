# This Python file uses the following encoding: utf-8
from QA import QA

qa = QA()
text = " من هو هاري بوتر؟"
context = """
هاري بوتر (بالإنجليزية: Harry Potter)‏ هو شخصية خيالية في سلسلة من سبعة كتب للكاتبة البريطانية ج. ك. رولنغ التي تحكي حكاية الصبي الساحر هاري بوتر، منذ اكتشافه لحقيقة كونه ساحراً، وحتى بلوغه سن السابعة عشر، فتكتشف ماضيه وعلاقاته السحريّة وسعيه للقضاء على سيد الظلام لورد فولدمورت. وترافق سلسلة الكتب سلسلة من ثمانية أفلام تحمل نفس عناوين الكتب. إن سلسلة هذا الفيلم تدور حول ولد يسمى هاري بوتر، يُقتل والداه وهو طفلٌ صغيرٌ على يد اللورد (فولدمورت) سيد الظلام. حققت سلسلة هاري بوتر نجاحاً هائلاً منذ صدور الجزء الأول منها هاري بوتر وحجر الفلاسفة في 26 حزيران (يونيو) 1998، وتُرجمت إلى معظم لغات العالم الحية ومنها اللغة العربية. بيع من الكتاب السادس هاري بوتر والأمير الهجين عشرة ملايين نسخة عشية صدوره، واعتُبر من أكثر الكتب مبيعاً في التاريخ، حتى صدور الكتاب السابع والنهائي من السلسلة هاري بوتر ومقدسات الموت الذي بيع منه ثمانية ملايين نسخة في الولايات المتحدة الأمريكية وحدها عشية صدوره في 21 يوليو 2007. اكتملت سلسلة كُتب هاري بوتر بصدور الكتاب السابع والنهائي، فيما أبدت المؤلفة رولنغ نيتها في عدم العودة إلى عالم هاري بوتر إلا لأغراض خيرية. أُنتج من الكتب 8 أفلام لتكتمل السلسلة، عُرض آخرها هاري بوتر ومقدسات الموت في 15 يوليو 2011.
"""
qa.answerQuestion(text, context)