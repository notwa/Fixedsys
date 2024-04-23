#!/usr/bin/python

# dewinfont is copyright 2001 Simon Tatham. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import string

# Extract bitmap font data from a Windows .FON or .FNT file.


def frombyte(s):
    return ord(s[0])


def fromword(s):
    return frombyte(s[0:1]) + 256 * frombyte(s[1:2])


def fromdword(s):
    return fromword(s[0:2]) | (fromword(s[2:4]) << 16)


def asciz(s):
    i = string.find(s, "\0")
    if i != -1:
        s = s[:i]
    return s


def bool(n):
    if n:
        return "yes"
    else:
        return "no"


class font:
    pass


class char:
    pass


def savefont(f, file):
    "Write out a .fd form of an internal font description."
    file.write("# .fd font description generated by dewinfont.\n\n")
    file.write("facename " + f.facename + "\n")
    file.write("copyright " + f.copyright + "\n\n")
    file.write("height " + "%d" % f.height + "\n")
    file.write("ascent " + "%d" % f.ascent + "\n")
    if f.height == f.pointsize:
        file.write("# ")
    file.write("pointsize " + "%d" % f.pointsize + "\n\n")
    if not f.italic:
        file.write("# ")
    file.write("italic " + bool(f.italic) + "\n")
    if not f.underline:
        file.write("# ")
    file.write("underline " + bool(f.underline) + "\n")
    if not f.strikeout:
        file.write("# ")
    file.write("strikeout " + bool(f.strikeout) + "\n")
    if f.weight == 400:
        file.write("# ")
    file.write("weight " + "%d" % f.weight + "\n\n")
    if f.charset == 0:
        file.write("# ")
    file.write("charset " + "%d" % f.charset + "\n\n")
    for i in range(256):
        file.write("char " + "%d" % i + "\nwidth " + "%d" % f.chars[i].width + "\n")
        if f.chars[i].width != 0:
            for j in range(f.height):
                v = f.chars[i].data[j]
                m = 1 << (f.chars[i].width - 1)
                for k in range(f.chars[i].width):
                    if v & m:
                        file.write("1")
                    else:
                        file.write("0")
                    v = v << 1
                file.write("\n")
        file.write("\n")


def dofnt(fnt):
    "Create an internal font description from a .FNT-shaped string."
    f = font()
    f.chars = [None] * 256
    version = fromword(fnt[0:])
    ftype = fromword(fnt[0x42:])
    if ftype & 1:
        sys.stderr.write("This font is a vector font\n")
        return None
    off_facename = fromdword(fnt[0x69:])
    if off_facename < 0 or off_facename > len(fnt):
        sys.stderr.write("Face name not contained within font data")
        return None
    f.facename = asciz(fnt[off_facename:])
    # print "Face name", f.facename
    f.copyright = asciz(fnt[6:66] + "\0")
    # print "Copyright", f.copyright
    f.pointsize = fromword(fnt[0x44:])
    # print "Point size", f.pointsize
    f.ascent = fromword(fnt[0x4A:])
    # print "Ascent", f.ascent
    f.height = fromword(fnt[0x58:])
    # print "Height", f.height
    f.italic = frombyte(fnt[0x50:]) != 0
    f.underline = frombyte(fnt[0x51:]) != 0
    f.strikeout = frombyte(fnt[0x52:]) != 0
    f.weight = fromword(fnt[0x53:])
    f.charset = frombyte(fnt[0x55:])
    # print "Attrs", f.italic, f.underline, f.strikeout, f.weight
    # print "Charset", f.charset
    # Read the char table.
    if version == 0x200:
        ctstart = 0x76
        ctsize = 4
    else:
        ctstart = 0x94
        ctsize = 6
    maxwidth = 0
    for i in range(256):
        f.chars[i] = char()
        f.chars[i].width = 0
        f.chars[i].data = [0] * f.height
    firstchar = frombyte(fnt[0x5F:])
    lastchar = frombyte(fnt[0x60:])
    for i in range(firstchar, lastchar + 1):
        entry = ctstart + ctsize * (i - firstchar)
        w = fromword(fnt[entry:])
        f.chars[i].width = w
        if ctsize == 4:
            off = fromword(fnt[entry + 2 :])
        else:
            off = fromdword(fnt[entry + 2 :])
        # print "Char", i, "width", w, "offset", off, "filelen", len(fnt)
        widthbytes = (w + 7) / 8
        for j in range(f.height):
            for k in range(widthbytes):
                bytepos = off + k * f.height + j
                # print bytepos, "->", hex(frombyte(fnt[bytepos:]))
                f.chars[i].data[j] = f.chars[i].data[j] << 8
                f.chars[i].data[j] = f.chars[i].data[j] | frombyte(fnt[bytepos:])
            f.chars[i].data[j] = f.chars[i].data[j] >> (8 * widthbytes - w)
    return f


def nefon(fon, neoff):
    "Finish splitting up a NE-format FON file."
    ret = []
    # Find the resource table.
    rtable = fromword(fon[neoff + 0x24 :])
    rtable = rtable + neoff
    # Read the shift count out of the resource table.
    shift = fromword(fon[rtable:])
    # Now loop over the rest of the resource table.
    p = rtable + 2
    while 1:
        rtype = fromword(fon[p:])
        if rtype == 0:
            break  # end of resource table
        count = fromword(fon[p + 2 :])
        p = p + 8  # type, count, 4 bytes reserved
        for i in range(count):
            start = fromword(fon[p:]) << shift
            size = fromword(fon[p + 2 :]) << shift
            if start < 0 or size < 0 or start + size > len(fon):
                sys.stderr.write("Resource overruns file boundaries\n")
                return None
            if rtype == 0x8008:  # this is an actual font
                # print "Font at", start, "size", size
                font = dofnt(fon[start : start + size])
                if font is None:
                    sys.stderr.write("Failed to read font resource at %x" % start)
                    return None
                ret = ret + [font]
            p = p + 12  # start, size, flags, name/id, 4 bytes reserved
    return ret


def pefon(fon, peoff):
    "Finish splitting up a PE-format FON file."
    dirtables = []
    dataentries = []

    def gotoffset(off, dirtables=dirtables, dataentries=dataentries):
        if off & 0x80000000:
            off = off & ~0x80000000
            dirtables.append(off)
        else:
            dataentries.append(off)

    def dodirtable(rsrc, off, rtype, gotoffset=gotoffset):
        number = fromword(rsrc[off + 12 :]) + fromword(rsrc[off + 14 :])
        for i in range(number):
            entry = off + 16 + 8 * i
            thetype = fromdword(rsrc[entry:])
            theoff = fromdword(rsrc[entry + 4 :])
            if rtype == -1 or rtype == thetype:
                gotoffset(theoff)

    # We could try finding the Resource Table entry in the Optional
    # Header, but it talks about RVAs instead of file offsets, so
    # it's probably easiest just to go straight to the section table.
    # So let's find the size of the Optional Header, which we can
    # then skip over to find the section table.
    secentries = fromword(fon[peoff + 0x06 :])
    sectable = peoff + 0x18 + fromword(fon[peoff + 0x14 :])
    for i in range(secentries):
        secentry = sectable + i * 0x28
        secname = asciz(fon[secentry : secentry + 8])
        secrva = fromdword(fon[secentry + 0x0C :])
        secsize = fromdword(fon[secentry + 0x10 :])
        secptr = fromdword(fon[secentry + 0x14 :])
        if secname == ".rsrc":
            break
    if secname != ".rsrc":
        sys.stderr.write("Unable to locate resource section\n")
        return None
    # Now we've found the resource section, let's throw away the rest.
    rsrc = fon[secptr : secptr + secsize]

    # Now the fun begins. To start with, we must find the initial
    # Resource Directory Table and look up type 0x08 (font) in it.
    # If it yields another Resource Directory Table, we stick the
    # address of that on a list. If it gives a Data Entry, we put
    # that in another list.
    dodirtable(rsrc, 0, 0x08)
    # Now process Resource Directory Tables until no more remain
    # in the list. For each of these tables, we accept _all_ entries
    # in it, and if they point to subtables we stick the subtables in
    # the list, and if they point to Data Entries we put those in
    # the other list.
    while len(dirtables) > 0:
        table = dirtables[0]
        del dirtables[0]
        dodirtable(rsrc, table, -1)  # accept all entries
    # Now we should be left with Resource Data Entries. Each of these
    # describes a font.
    ret = []
    for off in dataentries:
        rva = fromdword(rsrc[off:])
        start = rva - secrva
        size = fromdword(rsrc[off + 4 :])
        font = dofnt(rsrc[start : start + size])
        if font is None:
            sys.stderr.write("Failed to read font resource at %x" % start)
            return None
        ret = ret + [font]
    return ret


def dofon(fon):
    "Split a .FON up into .FNTs and pass each to dofnt."
    # Check the MZ header.
    if fon[0:2] != "MZ":
        sys.stderr.write("MZ signature not found\n")
        return None
    # Find the NE header.
    neoff = fromdword(fon[0x3C:])
    if fon[neoff : neoff + 2] == "NE":
        return nefon(fon, neoff)
    elif fon[neoff : neoff + 4] == "PE\0\0":
        return pefon(fon, neoff)
    else:
        sys.stderr.write("NE or PE signature not found\n")
        return None


def isfon(data):
    "Determine if a file is a .FON or a .FNT format font."
    if data[0:2] == "MZ":
        return 1  # FON
    else:
        return 0  # FNT


a = sys.argv[1:]
options = 1
outfile = None
prefix = None
infile = None
if len(a) == 0:
    print("usage: dewinfont [-o outfile | -p prefix] file")
    sys.exit(0)
while len(a) > 0:
    if a[0] == "--":
        options = 0
        a = a[1:]
    elif options and a[0][0:1] == "-":
        if a[0] == "-o":
            try:
                outfile = a[1]
                a = a[2:]
            except IndexError:
                sys.stderr.write("option -o requires an argument\n")
                sys.exit(1)
        elif a[0] == "-p":
            try:
                prefix = a[1]
                a = a[2:]
            except IndexError:
                sys.stderr.write("option -p requires an argument\n")
                sys.exit(1)
        else:
            sys.stderr.write("ignoring unrecognised option " + a[0] + "\n")
            a = a[1:]
    else:
        if infile is not None:
            sys.stderr.write("one input file at once, please\n")
            sys.exit(1)
        infile = a[0]
        a = a[1:]

fp = open(infile, "rb")
data = fp.read()
fp.close()

if isfon(data):
    fonts = dofon(data)
else:
    fonts = [dofnt(data)]

if len(fonts) > 1 and prefix is None:
    sys.stderr.write("more than one font in file; use -p prefix\n")
    sys.exit(1)
if outfile is None and prefix is None:
    sys.stderr.write("please specify -o outfile or -p prefix\n")
    sys.exit(1)

for i in range(len(fonts)):
    if len(fonts) == 1 and outfile is not None:
        fname = outfile
    else:
        fname = prefix + "%02d" % i + ".fd"
    fp = open(fname, "w")
    savefont(fonts[i], fp)
    fp.close()
