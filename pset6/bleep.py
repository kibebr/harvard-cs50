from sys import argv

def main():
	if not len(argv) == 2:
		print("usage: python bleep.py 'bannedwords.txt'")
	else:
		userInput = input("text you would like to bleep: ")
		bleep(userInput, argv[1])

def bleep(userText, filePath):
	textFile = open(filePath, "r")
	bannedWords = set()
	newUserText = ""

	for words in textFile:
		bannedWords.add(words.replace("\n", ""))

	for words in userText.split():
		if words.lower() in bannedWords:
			asterisks = ""
			for bleeps in range(len(words)):
				asterisks += "*"
			newUserText += (words.replace(words, asterisks)+" ")
		else:
			newUserText += (words+" ")

	print(newUserText)

if __name__ == "__main__":
    main()
