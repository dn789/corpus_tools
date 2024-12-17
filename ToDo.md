1. Clean up db.py a little bit maybe?
2. Fix documentation in process_doc.py
3. Integrate apache tika?
4. More elegant way of getting meta_label from meta_prop_ref

## Corpus processing

1. USE Corpus - Use BS4 to geet tags, need new method to parse non-XML tags
2. Handle arbitrarily nested meta properties
3. Decide what to do about list/set meta property values in .cha files (converting to string for now)
4. Figure out automatic conversion for plotting complex values (age/datetime, etc.) - Should be MetaProperty attribute of Corpus option
