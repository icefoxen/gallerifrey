#!/usr/bin/env python
# Gallerifrey
# Batch image gallery program
# Takes a directory of files and generates static HTML files, creates thumbnails, etc...
# Right now it processes all images in a directory, regardless of whether or not they already exist,
# and is in general pretty simple.
#
# Requires Debian package python-pythonmagick
#
# To do: Handle SVG?  Don't need thumbnails..
# Have some command line options... verbose, clobber non-image files...
# Query screen size and resize image in image page suitably???
#
# Alteration commands...  Rename, add to category/categories

# Change this to the appropriate directory.
ALBUMDIR = "/home/icefox/my.src/gallerifrey/album"
# Change this to the title you want
TITLE = "Gallerifrey"


#### DON'T CHANGE ANYTHING BELOW THIS ####
#### Unless you really want to.

import os
import shutil
import PythonMagick


CATEGORYFILE = os.path.join(ALBUMDIR, "categories.txt")
IMAGEDIR = os.path.join(ALBUMDIR, "images")
THUMBDIR = os.path.join(ALBUMDIR, "thumbs")
CATEGORYDIR = os.path.join(ALBUMDIR, "categories")
HTMLDIR = ALBUMDIR
INDEXFILE = os.path.join(ALBUMDIR, "index.html")

IMAGEFILES =  [".png", ".jpg", ".gif", ".tiff"]

def fileHasExt(f, extension):
    (_, ext) = os.path.splitext(f)
    return ext == extension

def getImagePageName(image):
    "Constructs an absolute page name for the given image."
    (basename, extension) = os.path.splitext(image)
    ifile = basename + ".html"
    return ifile

def getIndexPageName(category, n):
    return "index-{}-{}.html".format(category, n)

def prettyPageName(name):
    (basename, extension) = os.path.splitext(name)
    return basename

def getThumbnailName(image):
    return os.path.join("thumbs", image)

def getImageFiles(where=IMAGEDIR):
    "Returns a list of all image file names in the given dir (defaults to IMAGEDIR)."
    fs = os.listdir(where)
    accm = []
    for filename in fs:
        (basename, ext) = os.path.splitext(filename)
        if ext.lower() in IMAGEFILES:
            accm.append(filename)
    accm.sort()
    return accm

def getHTMLFiles(where=HTMLDIR):
    "Returns a list of all the .html files in the given dir (defaults to HTMLDIR)."
    fs = os.listdir(where)
    htmlfiles = [x for x in fs if fileHasExt(x, '.html')]
    return htmlfiles

THUMBSIZE = 128
def createThumbnails(images):
    """Makes thumbnail images for all the image files, in the THUMBDIR."""
    for i in images:
        infile = os.path.join(IMAGEDIR, i)
        outfile = os.path.join(THUMBDIR, i)
        # Skip already-existing thumbnails
        if os.path.isfile(outfile): continue
        
        a = PythonMagick.Image(infile)
        size = a.size()
        w = size.width()
        h = size.height()
        aspectRatio = float(w) / float(h)
        if aspectRatio > 1.0:
            # Resize based on width
            scalefactor = float(w) / THUMBSIZE
            height = int(h / scalefactor)
            g = PythonMagick.Geometry(THUMBSIZE, height)
        else:
            # Resize based on height
            scalefactor = float(h) / THUMBSIZE
            width = int(w / scalefactor)
            g = PythonMagick.Geometry(width, THUMBSIZE)
        a.resize(g)
        a.write(outfile)

def chunks(l, n):
    """Split a list into chunks of size n"""
    return [l[i:i+n] for i in range(0, len(l), n)]
    

def generateTable(items, cssclass, padding, numColumns):
    header = '\n<table class="{0}">\n<tr class="{0}">\n'.format(cssclass)
    footer = '\n</tr>\n</table>\n'
    cells = ['<td class="{0}">{1}</td>'.format(cssclass, x) for x in items]
    padding = '<td class="{0}">{1}</td>'.format(cssclass, padding)
    if len(cells) % numColumns == 0:
        padcount = 0
    else:
        padcount = numColumns - (len(cells) % numColumns)
    cells = cells + ([padding] * padcount)
    rowLists = chunks(cells, numColumns)
    rowStrings = ["".join(row) for row in rowLists]
    wholeShebang = "</tr>\n<tr>\n".join(rowStrings)
    return header + wholeShebang + footer


def generateCategoryTable(categories):
    """Returns an HTML table with links to all the categories given."""
    keys = categories.keys()
    keys.sort()
    itemstring = """
  <p><a href="{0}">{1} ({2})</a>
  </p>
"""
    items = [itemstring.format(
            getIndexPageName(item, 0), item, 
            len(categories[item])
            )
             for item in keys]
    header = '\n<table class="categorytable">\n<tr>\n'
    footer = '\n</tr>\n</table>'
    padding = '<td><p>&nbsp;</p></td>'
    return generateTable(items, "categorytable", "<p>&nbsp</p>", 10)
    
    #return '<p class="categoryList">' + ' | '.join(items) + '</p>'
        
    

def generateImageTable(images):
    """Returns an HTML table string linking to all the images given."""
    imgstring = """
    <p>
      <a href="{0}">
        <img src="{1}" border=1 alt="{1}">
      </a>
    </p>
    <p>{2}</p>
"""
    imgps = [
        imgstring.format(
             getImagePageName(image),
             getThumbnailName(image),
             image)
         for image in images]
    return generateTable(imgps, "imagetable", "<p> </p>", 4)

def setupAllIndexPages(categories):
    """Creates all index pages"""
    for c in categories:
        setupIndexPages(c, categories)

def setupIndexPages(category, categories):
    """Takes a category name and a set of categories, and creates
an index file for that category.
"""
    #print "Setting up index for", category
    imagesPerPage = 60
    catTable = generateCategoryTable(categories)
    header = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>{0}</title>
<link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
<h1>{0}</h1>
<h2>{1}</h2>
{2}
""".format(TITLE, category, catTable)
    images = categories[category]
    footer = """\n</body></html>"""
    
    imageChunks = chunks(images, imagesPerPage)
    numchunks = len(imageChunks)
    for (i,chunk) in enumerate(imageChunks):
        name = getIndexPageName(category, i)
        nextPage = getIndexPageName(category, (i+1) % numchunks)
        prevPage = getIndexPageName(category, (i-1) % numchunks)
        createIndexPage(name, category, catTable, nextPage, prevPage, chunk)

def createIndexPage(name, category, catlist, nextPage, prevPage, images):
    """Creates an index page with the given name and images, which
links to nextPage and prevPage"""
    template = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>{0}</title>
<link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
<h1>{0}</h1>
<h2>{1}</h2>
{2}
{3}
{4}
{3}
</body>
</html>
"""
    imgt = generateImageTable(images)
    nextprev = generateNextPrev(name, prettyPageName(name),
                                nextPage, prettyPageName(nextPage),
                                prevPage, prettyPageName(prevPage))
    outstr = template.format(TITLE, category, catlist, nextprev, imgt)
    fname = os.path.join(HTMLDIR, name)
    with open(fname, 'w') as f:
        f.write(outstr)

def generateNextPrev(current, currentName, next, nextName, prev, prevName):
    row = generateNextPrevRow(current, currentName, next, nextName, prev, prevName)
    return '<table border="1">\n' + row + '</table>'


def generateNextPrevRow(current, currentName, next, nextName, prev, prevName):
    linktext = '<tr>'
    linktext += '<td><a href="{0}">&lt;&lt; {1} &lt;&lt;</a></td>'.format(prev, prevName)
    linktext += '<td><a href="{0}"> {1} </a></td>'.format(current, currentName)
    linktext += '<td><a href="{0}">&gt;&gt; {1} &gt;&gt;</a></td>'.format(next, nextName)
    linktext += "</tr>"
    return linktext

def readCategories(images):
    """Reads the category files and returns a pair of tables listing all
relationships, the first by (category -> file set) and the second by
(file -> category set)
"""
    categoryFiles = os.listdir(CATEGORYDIR)
    categoryFiles = filter(lambda f: not os.path.isdir(f), categoryFiles)
    categoryFiles = filter(lambda f: not fileHasExt(f, '.bak'), categoryFiles)
    categoryFiles = filter(lambda f: not fileHasExt(f, '.tmp'), categoryFiles)
    imagesByCategory = {}
    categoriesByImage = {}
    # the 'all' category contains all images
    imagesByCategory['all'] = set(images)

    for i in images:
        categoriesByImage[i] = {'all'}
    # We also always have an 'uncategorized' category
    imagesByCategory['uncategorized'] = set()
    # Now we slurp up the category file and add all images
    # listed in it to that category
    for cf in categoryFiles:
        # We skip the auto-generated categories; they don't
        # read their contents from the files!
        if cf in ['all', 'uncategorized']:
            continue
        category = set()
        with open(os.path.join(CATEGORYDIR, cf)) as f:
            for imgname in f.xreadlines():
                imgname = imgname.strip()
                category.add(imgname)

                # While we are at it, we add that category to the
                # set of categories that image is in.
                if not categoriesByImage.has_key(imgname):
                    categoriesByImage[imgname] = set()
                categoriesByImage[imgname].add(cf)
        imagesByCategory[cf] = category
    
    # The 'uncategorized' category contains all images
    # without other defined categories.
    for (image,cats) in categoriesByImage.iteritems():
        num = len(cats)
        if num == 1:
            # Only the 'all' category, add 'uncategorized'
            categoriesByImage[image].add('uncategorized')
            imagesByCategory['uncategorized'].add(image)
        elif num > 2 and 'uncategorized' in cats:
            # We have 'all', 'uncategorized' and something else;
            # remove uncategorized.
            categoriesByImage[image].remove('uncategorized')
            imagesByCategory['uncategorized'].remove(image)

    # Though it is inelegant, we turn the sets into sorted lists here
    # since it is inevitable that we do so anyway for output, so we might
    # as well do it once all in the same place.
    ibyc = {}
    cbyi = {}
    for (c,i) in imagesByCategory.iteritems():
        l = list(i)
        l.sort()
        ibyc[c] = l
    for (i,c) in categoriesByImage.iteritems():
        l = list(c)
        l.sort()
        cbyi[i] = l
    return (ibyc, cbyi)


def readCategoriesOld(images):
    """Reads the category file and returns a pair of tables listing all
relationships, the first by (category -> file set) and the second by
(file -> category set)
"""
    lines = []
    try:
        with open(CATEGORYFILE, 'r') as f:
            lines = [l.strip().split(',') for l in f]
    except IOError:
        # It's okay if the category file doesn't exist.
        pass
    # These dicts are inverses of each other.
    # The key is an image or a category name, and the value is
    # a set of category or image names.
    imagesByCategory = {}
    categoriesByImage = {}
    # The 'all' category contains all images.
    imagesByCategory['all'] = set(images)
    for i in images:
        categoriesByImage[i] = {'all'}
    # We also always have an 'uncategorized' category.
    imagesByCategory['uncategorized'] = set()

    for line in lines:
        image = line[0]
        categories = set(line[1:])
        categories.add('all')
        categoriesByImage[image] = categories
    for (image,categories) in categoriesByImage.iteritems():
        for c in categories:
            if c in imagesByCategory:
                imagesByCategory[c].add(image)
            else:
                imagesByCategory[c] = {image}

    # The 'uncategorized' category contains all images
    # without other defined categories.
    for (image,cats) in categoriesByImage.iteritems():
        num = len(cats)
        if num == 1:
            # Only the 'all' category, add 'uncategorized'
            categoriesByImage[image].add('uncategorized')
            imagesByCategory['uncategorized'].add(image)
        elif num > 2 and 'uncategorized' in cats:
            # We have 'all', 'uncategorized' and something else;
            # remove uncategorized.
            categoriesByImage[image].remove('uncategorized')
            imagesByCategory['uncategorized'].remove(image)

    ibyc = {}
    cbyi = {}
    for (c,i) in imagesByCategory.iteritems():
        l = list(i)
        l.sort()
        ibyc[c] = l
    for (i,c) in categoriesByImage.iteritems():
        l = list(c)
        l.sort()
        cbyi[i] = l
    return (ibyc, cbyi)

def writeCategories(imagesByCategory):
    """Writes the given dictionary of (category -> image set)
to the category files."""
    for (catname, imgset) in imagesByCategory.iteritems():
        # Python sets have no defined iteration order.
        # So we do some shenanigans to make sure it's alphabetical.
        imglist = list(imgset)
        imglist.sort()
        catfilename = os.path.join(CATEGORYDIR, catname)
        bakfilename = catfilename + ".bak"
        tmpfilename = catfilename + ".tmp"
        with open(tmpfilename, 'w') as f:
            imglist = [x + '\n' for x in imglist]
            f.writelines(imglist)

        # Move temp file to real file
        try:
            shutil.copyfile(catfilename, bakfilename)
        except IOError:
            # It's okay if CATEGORYFILE doesn't exist
            pass
        os.rename(tmpfilename, catfilename)

def writeCategoriesOld(categoriesInImages):
    """Writes the given dictionary of (image -> category set)
to CATEGORYFILE, safely."""
    bakfile = CATEGORYFILE + ".bak"
    tmpfile = CATEGORYFILE + ".tmp"
    with open(tmpfile, 'w') as f:
        lst = [x for x in categoriesInImages.iteritems()]
        lst.sort()
        for (image, categories) in lst:
            clist = list(categories)
            clist.sort()
            l = [image] + clist
            outstr = ','.join(l) + '\n'
            f.write(outstr)
    try:
        shutil.copyfile(CATEGORYFILE, bakfile)
    except IOError:
        # It's okay if CATEGORYFILE doesn't exist
        pass
    os.rename(tmpfile, CATEGORYFILE)


def createImagePages(imgByCat, catByImage):
    """Creates all the image pages"""
    for (image,categories) in catByImage.iteritems():
        prevNextLinks = []
        for cat in categories:
            imagesInCat = imgByCat[cat]
            # XXX: This could be faster with a binary search maybe?
            #print "Category: {0}, image: {1}".format(cat, image)            
            #print imagesInCat
            imgidx = imagesInCat.index(image)
            numImages = len(imagesInCat)
            previmg = imagesInCat[(imgidx - 1) % numImages]
            nextimg = imagesInCat[(imgidx + 1) % numImages]
            prevNextLinks.append((cat, nextimg, previmg))
        
        imgtext  = generateImagePage(image, prevNextLinks)
        pagename = os.path.join(HTMLDIR, getImagePageName(image))
        with open(pagename, 'w') as f:
            f.write(imgtext)

def generateImagePage(image, links):
    """Creates the HTML for a single image page."""
    # 'links' is a list of (category, next, prev) tuples
    links.sort()
    accm = ['<table border="1">']
    for (cat, next, prev) in links:
        catpage = getIndexPageName(cat, 0)
        nextpage = getImagePageName(next)
        prevpage = getImagePageName(prev)
        accm.append(generateNextPrevRow(catpage, cat, nextpage, next, prevpage, prev))
    accm.append("</table>")
    linktext = '\n'.join(accm)

    text = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>{0}</title>
<link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
<h1>{0}</h1>
<p>
<a href="images/{0}">
<img src="images/{0}" height="70%%" alt="{0}">
</a>
</p>
{1}
</body>
</html>
    """.format(image, linktext)
    return text


def createHTML(images):
    print("Generating categories...")
    (imagesByCategory, categoriesByImage) = readCategories(images)
    writeCategories(imagesByCategory)
    print("Generating index pages...")
    setupAllIndexPages(imagesByCategory)
    print("Generating image pages...")
    createImagePages(imagesByCategory, categoriesByImage)


def cleanOldFiles():
    """Cleans up unused thumbnails
and image pages.
It also nukes all the HTML pages, but those get
re-made every time anyway."""
    imgs = set(getImageFiles())
    thumbs = set(getImageFiles(where=THUMBDIR))
    leftoverThumbs = thumbs - imgs
    htmlfiles = getHTMLFiles()
    print "Deleting old HTML and {0} old thumbnails...".format(len(leftoverThumbs))    
    for i in leftoverThumbs: os.remove(os.path.join(THUMBDIR, i))
    for i in htmlfiles: os.remove(os.path.join(HTMLDIR, i))



def main():
    imgs = getImageFiles()
    print("Ok, processing %s images..." % len(imgs))
    cleanOldFiles()
    print("Generating thumbnails...")
    createThumbnails(imgs)
    print("Generating pages...")
    createHTML(imgs)
    firstindex = os.path.join(ALBUMDIR, getIndexPageName("all", 0))
    shutil.copyfile(firstindex, INDEXFILE)
    print("Done!")

###############################################################
### Below here are utility functions for doing specific things.
### They are too rarified to be generally necessary, but are 
### useful for maintenance tasks.
###############################################################

def keyDiff(d1, d2):
    d1k = set(d1.keys())
    d2k = set(d2.keys())
    return d1k - d2k

def valsMatch(d1, d2):
    for k in d1.keys():
        if set(d1[k]) != set(d2[k]):
            print "Different values for key", k
            return False
    return True

def convertCategories():
    """Convert the old one-image-per-line-of-file category format
to the new format where each category is a file with image names.
You still need to create the category dir."""
    imgs = getImageFiles()
    print "Reading old categories"
    (c1,f1) = readCategoriesOld(imgs)
    print "Writing new categories"
    writeCategories(c1)
    print "Re-reading new categories"
    (c2, f2) = readCategories(imgs)
    print "Verifying..."
    fkdiff = keyDiff(f1, f2)
    if len(fkdiff) == 0: print "File keys match"
    if valsMatch(f1, f2): print "File values match"
    
    ckdiff = keyDiff(c1, c2)
    if len(ckdiff) == 0: print "Category keys match"
    if valsMatch(c1, c2): print "Category values match"


if __name__ == '__main__':
    main()
