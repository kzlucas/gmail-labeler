import argparse
import gmails_scrapper
import classifier
import gmail_set_labels

def main():
    parser = argparse.ArgumentParser(description='Gmail Labeler')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # build-db command
    build_db_parser = subparsers.add_parser('build-db', help='Build database')
    build_db_parser.add_argument('--after', type=str, help='Fetch emails after this date (YYYY/MM/DD)')
    build_db_parser.add_argument('--before', type=str, help='Fetch emails before this date (YYYY/MM/DD)')
    build_db_parser.add_argument('--batches-count', type=int, help='Limit max number of fetch batches')
    build_db_parser.add_argument('--batches-size', type=int, help='Limit number of emails per batch. Default is 20')
    
    # get_embeddings command
    get_embeddings_parser = subparsers.add_parser('get-embeddings', help='Get emails embeddings')
    
    # classify command
    classify_parser = subparsers.add_parser('classify', help='Classify emails')
    classify_parser.add_argument('--drop-existing', action='store_true', help='Drop existing classification and clusters before classifying')
    
    # apply-labels command
    apply_labels_parser = subparsers.add_parser('apply-labels', help='Apply labels to emails in Gmail')
    
    args = parser.parse_args()
    
    if args.command == 'build-db':
        print(f"Building database with args: {args}")
        gmails_scrapper.run(
            AFTER=args.after or "1970/01/01",
            BEFORE=args.before or "2048/01/01",
            BATCHES_COUNT=args.batches_count or 999999,
            BATCHES_SIZE=args.batches_size or 20
        )
        
    elif args.command == 'get-embeddings':
        print(f"Getting emails embeddings...")
        classifier.get_embeddings()
        
    elif args.command == 'apply-labels':
        print(f"Applying labels to emails in Gmail...")
        gmail_set_labels.run()
        
    elif args.command == 'classify':
        print(f"Classifying...")
        classifier.run()
    else:
        print("--" * 20)
        print("Use [command] --help for more information on a command and its arguments.")
        print("--" * 20)
        parser.print_help()


if __name__ == '__main__':
    main()
