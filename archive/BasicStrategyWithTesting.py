    def BasicTextStrategy(self) -> List:
        """
        Load the documents using the a basic PDF Loader, i.e PyMuPDF. This strategy is used for documents that are mostly text.
        It does not work well with table and mathematical formulas like LaTex.

        Returns:
          List[Doucment]: A list of loaded documents with metadata.
        """
        docs_cnt = 0
        for file in os.listdir(self.folder_path):
            if not file.endswith(".pdf"):
                continue
            if file.endswith(".json"):
                self.documents.append(self.load_docs_from_json(file))
                continue
            filepath = os.path.join(self.folder_path, file)
            try:
                # for testing purposes - use this in the final version # self.documents.append(PyMuPDFLoader(filepath).load())
                # extracted_doc = PyMuPDFLoader(filepath).load()
                self.documents.append(PyMuPDFLoader(filepath).load())

                self.documents.append(extracted_doc)
                # Save the extracted text (page_content=[...]) into a txt file for viewing
                self.store_extracted_text(
                    extracted_doc, filepath, "extracted_text_for_viewing"
                )
                # Save the extracted text to a JSON file for viewing
                # Not implemented yet
                docs_cnt += 1
            except Exception as e:
                print(f"Error reading {file} with Error: {e}")
        print("Number of loaded documents:", docs_cnt)
        return self.documents