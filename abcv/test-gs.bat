gs -o output.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress -dHaveTrueTypes=true -dEmbedAllFonts=true -dSubsetFonts=false -c ".setpdfwrite <</NeverEmbed [ ]>> setdistillerparams" -f input.ps
