import os, json, math, argparse, shutil

# Valid extensions to consider
extensions = ("in", "dat", "out", "ans")

# Find all files needed
def search(directory: str):
	if debug: print("Searching:", os.path.join(os.path.abspath(directory), ""))

	# Get all files in the directory
	(_, _, files) = next(os.walk(directory))

	# All questions gotten
	# Format:
	#  Key - Question name
	#  Value - List:
	#   0 - Input extension (in/dat) (Can be None)
	#   1 - Output extension (out/ans)
	questions = {}

	for file in files:

		# Get the file extension
		extension = file[file.rindex(".") + 1:]

		# If the extension isn't in the list, skip
		if extension not in extensions: continue

		# Figure out if it's an input/data (0) or output/answer (1)
		index = math.floor(extensions.index(extension) / 2)

		# Make file just the filename
		file = file[:file.rindex(".")]

		# If the file isn't a registered question, add it
		if file not in questions:
			questions[file] = [None, None]

		data = questions[file]

		# If data has already been set for input/data or output/answer
		if data[index] is not None:
			if debug: print("Multiple ", ("output/answer" if index else "input/data"), " files detected for \"", file, '"', sep="")

			if force: continue
			else: return None
		else:
			# Save which extension is used
			data[index] = extension

	for question, fileExtensions in questions.items():
		# Make sure it has an output/answer file
		if fileExtensions[1] is None:
			if debug: print("Question \"", question, "\" doesn't have an output/answer", sep="")

			if force: continue
			else: return None

	# Return questions gotten
	return questions

# Proxy call to isdir
def isDirectory(path: str):
	return os.path.isdir(path)

# Proxy call to isfile
def isFile(path: str):
	return os.path.isfile(path)

# Gets a folder that exists
def getFolder(prompt: str):
	# Loop until a directory that exists is provided
	while not isDirectory((path := input(prompt))): pass
	return path

# Proxy call to copy2
def copy(src: str, dest: str):
	return shutil.copy2(src, dest)

# Proxy call to mkdir
def mkdir(path: str):
	# If path already exists
	if isDirectory(path): return True

	os.mkdir(path, 0o755)
	return isDirectory(path)

# Program main
def main(args: argparse.Namespace):
	# Define globals
	global force, debug
	force = args.force
	debug = args.debug

	# If no path or the path isn't a directory
	if not (args.path and isDirectory(args.path)):
		args.path = getFolder("Path to data: ")

	# If not destination or (path isn't a directory and shouldn't make the destination if it doesn't exist)
	if not (args.dest and (args.mkdir or isDirectory(args.dest))):
		args.dest = getFolder("Path to destination: ")

	# Get absolute paths
	args.path = os.path.join(os.path.abspath(args.path), "")
	args.dest = os.path.join(os.path.abspath(args.dest), "")

	# If we should make the destination and after mkdir the folder doesn't exist
	if args.mkdir and not mkdir(args.dest):
		if debug: print("Couldn't make the destination folder")
		if not force: return

	# If we should clean to destination folder
	if args.clean:
		fail = False

		# Error handler for rmtree
		def onError(func, path, excInfo):
			if debug: print("Unable to delete \"", path, '"', sep="")
			if not force: fail = True

		# Get all directories and files within the destination folder
		for root, directories, files in os.walk(args.dest):

			# Loop over directories
			for directory in directories:
				if fail: break

				# Remove everything in the directory and the directory itself
				shutil.rmtree(os.path.join(root, directory), ignore_errors=False, onerror=onError)

			if fail: return

			#Loop over files
			for file in files:
				# Detele file
				os.unlink(os.path.join(root, file))
		if fail: return

	# Search the path for data
	questions = search(args.path)

	# Data found had issues
	if questions is None:
		print("Unable to read question data from \"", args.path, '"', sep="")
		return

	if debug:
		print("Loaded data:")
		# Get question name and extensions
		for question, fileExtensions in questions.items():
			print("\t", question, ": ", "{:<5}".format(fileExtensions[0] if fileExtensions[0] is not None else "null"), "/", "{:>5}".format(fileExtensions[1] if fileExtensions[1] is not None else "null"), sep="")

	# If the server data folder doesn't exist after trying to create it
	if not mkdir(f"{args.dest}Server Data/"):
		if debug: print("Unable to make Server Data folder")
		if not force: return

	# Get all the folders and files in the server data folder in the destination
	items = os.listdir(f"{args.dest}Server Data/")

	# If it has any directories or files in it
	if len(items):
		if debug:
			if args.clean:
				print("Failed to clean the server data folder")
			else:
				print("Server data folder already contained some data")

		if not force: return


	# If judge data folder doesn't exist after trying to create it
	if not mkdir(f"{args.dest}Judge Data/"):
		if debug: print("Unable to make Judge Data folder")
		if not force: return

	# Get all the folders and files in the judge data folder in the destination
	items = os.listdir(os.path.join(args.dest, "Judge Data", ""))

	# If it has any directories or files in it
	if len(items):
		if debug:
			if args.clean:
				print("Failed to clean the judge data folder")
			else:
				print("Judge data folder already contained some data")

		if not force: return

	# Delete results from walk
	del items

	# Loop over the question and extensions
	for question, fileExtensions in questions.items():

		# If the question directory doesn't exist after trying to create it
		if not mkdir(os.path.join(args.dest, "Server Data", question, "")):
			if debug: print("Unable to create question folder in Server Data folder")
			if force: continue
			else: return

		# If there was a file extension found for input/data
		if fileExtensions[0] is not None:
			dat = os.path.join(args.path, f"{question}.{fileExtensions[0]}")
			serverDat = os.path.join(args.dest, "Server Data", question, f"{question}.dat")

			if debug > 1: print(f"Copying \"{dat}\" to \"{serverDat}\"")
			# Copy to server data
			copy(dat, serverDat)

			# If copied file doesn't exist
			if not isFile(serverDat):
				if debug: print(f"Failed to copy {question}'s data file to the server's data")

				if force: continue
				else: return

			judgeDat = os.path.join(args.dest, "Judge Data", f"{question}.dat")

			if debug > 1: print(f"Copying \"{dat}\" to \"{judgeDat}\"")
			# Copy to judge data
			copy(dat, judgeDat)

			# If copied file doens't exist
			if not isFile(judgeDat):
				if debug: print(f"Failed to copy {question}'s data file to the judge's data")

				if force: continue
				else: return

		# If there was a file extension found for output/answer
		if fileExtensions[1] is not None:
			ans = f"{args.path}{question}.{fileExtensions[1]}"
			serverAns = f"{args.dest}Server Data/{question}/{question}.ans"

			if debug > 1: print(f"Copying \"{ans}\" to \"{serverAns}\"")
			# Copy to server data
			copy(ans, serverAns)

			# If copied file doesn't exist
			if not isFile(serverAns):
				if debug: print(f"Failed to copy {question}'s answer file to the server's data")

				if force: continue
				else: return

			judgeAns = f"{args.dest}Judge Data/{question}.ans"

			if debug > 1: print(f"Copying \"{ans}\" to \"{judgeAns}\"")
			# Copy to judge data
			copy(ans, judgeAns)

			# If copied file doesn't exist
			if not isFile(judgeAns):
				if debug: print(f"Failed to copy {question}'s answer file to the judge's data")

				if force: continue
				else: return

# If script is being directly executed
if __name__ == "__main__":
	# Setup argument parser
	parser = argparse.ArgumentParser()
	parser.add_argument("--path", help="Path to data")
	parser.add_argument("--dest", help="Path to destination (root folder)")
	parser.add_argument("--force", help="Ignore problems and continue", action="store_true")
	parser.add_argument("--debug", help="Enables debugging", default=0, choices=(1, 2), type=int)
	parser.add_argument("--clean", help="Clear out destination", action="store_true")
	parser.add_argument("--mkdir", help="Create destination path if it doesn't exist", action="store_true")

	# Start program and pass in parsed arguments
	main(parser.parse_args())
