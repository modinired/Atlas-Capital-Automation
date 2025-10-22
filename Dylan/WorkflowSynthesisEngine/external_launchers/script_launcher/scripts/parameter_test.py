
import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to test various parameter types.")

    parser.add_argument("--name", type=str, required=True, help="Your name.")
    parser.add_argument("--age", type=int, default=30, help="Your age.")
    parser.add_argument("--height", type=float, help="Your height in meters.")
    parser.add_argument("--is_student", action="store_true", help="Are you a student?")
    parser.add_argument("--input_file", type=str, help="Path to an input file.")

    args = parser.parse_args()

    print(f"Hello, {args.name}!")
    print(f"You are {args.age} years old.")

    if args.height:
        print(f"You are {args.height} meters tall.")

    if args.is_student:
        print("You are a student.")
    else:
        print("You are not a student.")

    if args.input_file:
        print(f"Input file path: {args.input_file}")
        try:
            with open(args.input_file, 'r') as f:
                print("First line of the file:")
                print(f.readline().strip())
        except Exception as e:
            print(f"Could not read the file: {e}")

    print("\nScript finished successfully!")

