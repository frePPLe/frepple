/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

<script setup lang="js">
import { useI18n } from 'vue-i18n';
import { useForecastsStore } from '@/stores/forecastsStore';
import {debouncedInputHandler, dateFormat, timeFormat} from "@common/utils.js";

const { t: ttt, locale, availableLocales } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});

const store = useForecastsStore();

function getComments() {
  return store.comments;
}

function setCommentType(newCommentType) {
  store.setCommentType(newCommentType);
}

// Create a debounced handler for comment input changes
const handleCommentChange = debouncedInputHandler(() => {
  store.updateCommentContent(store.newComment);
}, 300);

const translateCommentHeaderString = (commentString) => {
  const commentParts = commentString.split(' ');

  commentParts[0] = ((commentParts[0] === 'itemlocation') ? ttt('item-location') : ttt(commentParts[0])) + ':';
  return commentParts.join(' ');
}

</script>

<template>
  <div id="commentsdata" class="clear">
    <div class="row">
      <div class="col">
        <div style="clear: both;">
          <input type="submit" role="button" id="commentitem" :value="ttt('new item comment')" v-on:click="setCommentType('item')" aria-disabled="false" :class="(store.commentType==='item') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">
          <input type="submit" role="button" id="commentitemlocation" :value="ttt('new item-location comment')" v-on:click="setCommentType('itemlocation')" aria-disabled="false" :class="(store.commentType==='itemlocation') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">
          <input type="submit" role="button" id="commentlocation" :value="ttt('new location comment')" v-on:click="setCommentType('location')" aria-disabled="false" :class="(store.commentType==='location') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">
          <input type="submit" role="button" id="commentcustomer" :value="ttt('new customer comment')" v-on:click="setCommentType('customer')" aria-disabled="false" :class="(store.commentType==='customer') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">

          <textarea
            class="form-control mt-2 mb-2"
            style="resize: vertical; width: 100%;"
            v-show="store.commentType"
            id="newcomment"
            rows="5"
            v-model="store.newComment"
            @input="handleCommentChange"
            :placeholder="ttt('Enter your comment here...')">
          </textarea><br>

          <div v-if="getComments().length > 0">
            <div :id="'pastcomments'+index" v-for="(record,index) in getComments()" :key="index">
              <hr>
              <h3 class="text-capitalize">{{record.user}}&nbsp;-&nbsp;{{ translateCommentHeaderString(record.type) }}</h3>
              <span class="float_right">{{dateFormat(record.lastmodified)}} {{timeFormat(record.lastmodified)}}</span>
              <pre>{{ record.comment }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
