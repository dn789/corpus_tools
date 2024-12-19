1. Clean up db.py a little.

## Corpus processing

1. USE Corpus - Use BS4 to get tags, need new method to parse non-XML tags
2. Handle arbitrarily nested meta properties
3. Decide what to do about list/set meta property values in .cha files (converting to string for now)
4. Figure out automatic conversion for plotting complex values (age/datetime, etc.) - Should be MetaProperty attribute
5. Integrate apache tika?
6. Fix documentation in process_doc.py
7. Handle value types in database (currently converting to string)
