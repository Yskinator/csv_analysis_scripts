# csv_analysis_scripts
A compilation of ugly hacks designed to make sense of some absurdly large csv files.

## Usage:

### Install dependencies:

pip install -r requirements.txt


### Plop in the required csvs:

combined_stock_master_withbrands.csv

unspsc_codes_3.csv

excluded_segments.csv


### Create an environment variable LOCAL if not running on azure functions. This is needed because imports are handled differently there.

### Linux:

in ~/.bashrc

export LOCAL="LOCAL"

### Other:

Google "create environmen variable [your operating system]"

### Generate the rest of the required csvs:
python constant_csv_generator.py


### Run the script:

#level denotes the level to operate the initial matching at.

#num_to_check determines the amount of top categories that are checked first.

Note: That's two required arguments too many, make the last two optional!

$ python csv_scripts.py filename.csv level[Segment, Family, Class] num_to_check[int]




## Git practices:

No new code should be written in the master branch. New branches should be made for each high level task, such as "Optimized code for handling single rows" or "Made commodity matching check other top categories if the first ones gave no good matches". These branches should be named something descriptive, such as "single_row_optimization" and "other_category_commodity_matching".

No code should be added to the master branch without first being reviewed by someone else. Instead, once your branch is done, make a pull request on GitHub, and wait for someone to go through your changes. They will then look for any issues with the code, and point them out so they can be fixed before the code is allowed on the master branch. Based on past experience, there should always be something that needs fixing - if nothing was found, the reviewer wasn't thorough enough!

## Git commands:

### Get new branch from GitHub:

git checkout --track origin/[desired_branch]

### Switch between branches:

git checkout [desired_branch]

### Create new branch:

git checkout [branch_from_which_we_branch]

git pull -r

git checkout -b [name_of_new_branch]

(Make your changes. No more than a handful of commits, each of which should only change one thing. If there's an "and" in your commit message, it needs to be two commits.)

git push -u origin [name_of_new_branch]

(Now go to the GitHub repository at https://github.com/Yskinator/csv_analysis_scripts, and click Pull requests just below the repository name. Click the big green New pull request button, compate master <- your_branch, and click the Create pull request button. The name of the pull request should explain what it is supposed to change, eg. "Optimized code for handling single rows". Add further comments if needed, and click Create pull request once more. Wait for someone to look through your code and leave comments, and implement any changes as required. Once that's done, your code will be merged into master.)

### Creating a new commit:

Staging:

git add -i

Choose patch:

p

Choose files:

1

2

...

[empty row]

Pick the changes you want to include:

y(yes)/n(no)/s(split)/e(edit)/..

Once done, exit the interactive staging with q

### Add new files:

git add [filename - tab auto completion is handy]

### Commit:

git commit -m "[descriptive commit message - if you needed 'and', it should be two commits]"

### Pushing to git:

1. Only if it works locally!

2. Always if it works locally. Try to keep the repository up to date.

Pull changes, use -r to avoid unnecessary merges. Check that your code still works! Then push.

git pull -r

git push

### Pulling new code from git:

git checkout [branch_name]

git pull -r

### Removing branches once you're done with them:

git branch -d [branch_name]

(Branches on GitHub will be deleted after a finished pull request, unless otherwise requested. They can also be manually removed under branches.)

### Getting updates from [parent_branch] to [your_branch]:

First pull the changes:

git checkout [parent_branch]

git pull -r

If your branch has been pushed to GitHub:

git checkout [your_branch]

git merge [parent_branch]

If your branch only exists locally:

git checkout [your_branch]

git rebase [parent_branch]

### Cherry-pick a specific commit from a specific branch:

git checkout [branch_with_commit]

git log

(Copy the hash of the desired commit)

git checkout [your_branch]

git cherry-pick [hash_you_copied]

### Revert a commit:

git log

(Copy the hash of the desired commit)

git revert [hash_you_copied]

### Editing an existing commit:

If the commit has been pushed to GitHub, DON'T! If it only exists locally, just make another commit instead. If it only exists locally, and you really really want to:

Changing the last commit:

git add [things you want to add]

git commit --amend

Editing older commits:

Reconsider your life choices.

### Doing things not included here:

Google "git doing-the-thing-I-want" and figure it out.
