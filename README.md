# Link Preview Smart Chips for Google Docs

This is the code base for a google ad on (see here: https://www.matthewjurow.com/software-projects/link-preview-smart-chips) that enables the new smart chip functionality for GitHub and StackExchange links pasted into google documents.

If enabled the program will display a bunch of information about a GitHub or StackExchange link when you mouse over and will allow you to send the ReadMe to a LLM AI model to summarize with the click of a button.  

Do be patient, I chose a strong model to summarize the text (facebook bart-large-cnn) so summarizing can sometimes take ten or twenty seconds depending on how much compute i have the back end set to allocate on any given day

! this code is lightly edited from the actual deployment to shield some of the security stuff // so if you have any recomended changes i'll input them by hand after review
! the complexity in the summary function is mostly to limit the size of the ReadMe input to avoid maxing out the token limits. if you need something truly huge summarized let me know and i'll send you the script modifications to chunk it out into bites and sew it back together
