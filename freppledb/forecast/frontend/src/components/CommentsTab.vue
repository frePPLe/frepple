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
import { useForecastsStore } from '@/stores/forecastsStore';

const store = useForecastsStore();

function getComments(commentType) {
  return store.comments;
}
</script>

<template>
  <div id="commentsdata" class="clear">
    <div class="row">

      <div class="col">
        <div style="clear: both;">
          <input type="submit" role="button" id="commentitem" value="new item comment" :click="getComments('item')" aria-disabled="false" style="font-size:12px" :class="commenttype=='item' ? 'active': 'inactive'" class="btn btn-primary text-capitalize">
          <input type="submit" role="button" id="commentitemlocation" value="new item-location comment" :click="getComments('itemlocation')" aria-disabled="false" style="font-size:12px" :class="commenttype=='itemlocation' ? 'active': 'inactive'" class="btn btn-primary text-capitalize">
          <input type="submit" role="button" id="commentlocation" value="new location comment" :click="getComments('location')" aria-disabled="false" style="font-size:12px" :class="commenttype=='location' ? 'active': 'inactive'" class="btn btn-primary text-capitalize">
          <input type="submit" role="button" id="commentcustomer" value="new customer comment" :click="getComments('customer')" aria-disabled="false" style="font-size:12px" :class="commenttype=='customer' ? 'active': 'inactive'" class="btn btn-primary text-capitalize">
          <textarea class="form-control mt-2 mb-2" style="resize: vertical; width: 100%;" v-show="commenttype" id="newcomment" rows="5" data-ng-model="newcomment" data-ng-change="changes = true" data-ng-model-options="{debounce: 300}"></textarea><br>
          <!-- ngIf: detaildata.comments.length==0; -->
          <!-- ngRepeat: record in detaildata.comments --><!-- ngIf: detaildata.comments.length>0; --><span id="pastcomments" data-ng-if="detaildata.comments.length&gt;0;" data-ng-repeat="record in detaildata.comments" class="ng-scope">
            <hr>
            <h3 class="ng-binding">admin ()&nbsp;customer All customers</h3>
            <span class="float_right ng-binding">2025-09-24 11:52:19.576841</span>
            <pre class="ng-binding">1 customer comment</pre>
          </span><!-- end ngIf: detaildata.comments.length>0; --><!-- end ngRepeat: record in detaildata.comments --><!-- ngIf: detaildata.comments.length>0; --><span id="pastcomments" data-ng-if="detaildata.comments.length&gt;0;" data-ng-repeat="record in detaildata.comments" class="ng-scope">
            <hr>
            <h3 class="ng-binding">admin ()&nbsp;location All locations</h3>
            <span class="float_right ng-binding">2025-09-24 11:52:09.372785</span>
            <pre class="ng-binding">1 location comment</pre>
          </span><!-- end ngIf: detaildata.comments.length>0; --><!-- end ngRepeat: record in detaildata.comments --><!-- ngIf: detaildata.comments.length>0; --><span id="pastcomments" data-ng-if="detaildata.comments.length&gt;0;" data-ng-repeat="record in detaildata.comments" class="ng-scope">
            <hr>
            <h3 class="ng-binding">admin ()&nbsp;itemlocation All items @ All locations</h3>
            <span class="float_right ng-binding">2025-09-24 11:51:56.889642</span>
            <pre class="ng-binding">1 Item-location comment</pre>
          </span><!-- end ngIf: detaildata.comments.length>0; --><!-- end ngRepeat: record in detaildata.comments --><!-- ngIf: detaildata.comments.length>0; --><span id="pastcomments" data-ng-if="detaildata.comments.length&gt;0;" data-ng-repeat="record in detaildata.comments" class="ng-scope">
            <hr>
            <h3 class="ng-binding">admin ()&nbsp;item All items</h3>
            <span class="float_right ng-binding">2025-09-24 11:51:33.922027</span>
            <pre class="ng-binding">1 Item comment</pre>
          </span><!-- end ngIf: detaildata.comments.length>0; --><!-- end ngRepeat: record in detaildata.comments -->
        </div>
      </div>

    </div>
  </div>
</template>

