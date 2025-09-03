from d3blobgen import get_d3_function_blob
from d3blobgen.scripts.example import mrset_fn_with_args, mrset_fn_without_args

def main():
    blob1 = get_d3_function_blob(mrset_fn_with_args, {"mr_set_name":"abc"})
    blob2  = get_d3_function_blob(mrset_fn_without_args)

    print("\nblob1 example =================================================================")
    print(blob1)
    
    print("\nblob2 example =================================================================")
    print(blob2)


if __name__ == "__main__":
    main()
