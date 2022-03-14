# embed_xmp_sidecars
for raw photo editing, embed sidecar files into images via a wrapper around exiftool

Problem:
  I want to backup my images and edits in amazon prime photos, but prime photos does not consider xmp(sidecar files) 
  as image files and I dont want to pay any exta for non image storage.
  
Solution:
  Embed the xmp files into the image's exif metadata. Prime photos doesnt know the diffrence.
  Be able to extract and recreate the origional xmp files.
  
 Applications sidecar's supported:
  Exposure x6
