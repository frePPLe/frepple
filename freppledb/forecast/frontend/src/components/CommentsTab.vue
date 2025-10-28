/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

<script setup lang="js">
import { useI18n } from 'vue-i18n';
import { useForecastsStore } from '@/stores/forecastsStore';
import {debouncedInputHandler} from "@common/utils.js";

const { t, locale, availableLocales } = useI18n({
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

const comments1 = [{"user": "admin ()", "lastmodified": "2025-09-25 06:20:14.060816", "comment": "customer comment 0", "type": "customer All customers"}, {"user": "admin ()", "lastmodified": "2025-09-25 06:20:02.677456", "comment": "location comment 0", "type": "location All locations"}, {"user": "admin ()", "lastmodified": "2025-09-25 06:19:54.072498", "comment": "Item-location comment 0", "type": "itemlocation All items @ All locations"}, {"user": "admin ()", "lastmodified": "2025-09-25 06:19:42.209849", "comment": "Item comment 0", "type": "item All items"}];
</script>

<template>
  <div id="commentsdata" class="clear">
    <div class="row">
      <div class="col">
        <div style="clear: both;">
          <input type="submit" role="button" id="commentitem" :value="t('new item comment')" v-on:click="setCommentType('item')" aria-disabled="false" :class="(store.commentType==='item') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">
          <input type="submit" role="button" id="commentitemlocation" :value="t('new item-location comment')" v-on:click="setCommentType('itemlocation')" aria-disabled="false" :class="(store.commentType==='itemlocation') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">
          <input type="submit" role="button" id="commentlocation" :value="t('new location comment')" v-on:click="setCommentType('location')" aria-disabled="false" :class="(store.commentType==='location') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">
          <input type="submit" role="button" id="commentcustomer" :value="t('new customer comment')" v-on:click="setCommentType('customer')" aria-disabled="false" :class="(store.commentType==='customer') ? 'active': 'inactive'" class="btn btn-primary text-capitalize me-1">

          <textarea
            class="form-control mt-2 mb-2"
            style="resize: vertical; width: 100%;"
            v-show="store.commentType"
            id="newcomment"
            rows="5"
            v-model="store.newComment"
            @input="handleCommentChange"
            :placeholder="t('Enter your comment here...')">
          </textarea><br>

          <div v-if="getComments().length > 0">
            <div :id="'pastcomments'+index" v-for="(record,index) in getComments()" :key="index">
              <hr>
              <h3>{{record.user}}&nbsp;{{ t('record.type') }}</h3>
              <span class="float_right">{{record.lastmodified}}</span>
              <pre>{{ record.comment }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
